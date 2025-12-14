# -*- coding: utf-8 -*-
"""行情数据客户端"""
import time
from openctp_ctp import thostmduserapi as mdapi

# 自定义模块
from utils.signal import (
    EXIT_FLAG, register_signals,
    wait_for_exit
)
from utils.context import CTPAPIContext, BackgroundThreadContext, AppContext
from config import (
    STREAM_PATH, IS_PRODUCTION_MODE, get_server_config
)
from controller import MarketDataController
from utils.logger import main_logger


def _trading_event_loop(ctp_api):
    """交易事件循环"""
    try:
        while not EXIT_FLAG.is_set():
            # 使用更短的轮询间隔，提高响应速度
            time.sleep(0.01)
    finally:
        ctp_api.Join()
        main_logger.debug("Main", "Trading event loop stopped")


class MarketDataClient:
    """
    行情数据客户端
    负责行情数据收集和处理
    """

    def __init__(self):
        """初始化：注册信号监听"""
        register_signals()

    def _setup_api(self, ctp_api, platform, env, exchanges="all", app_context=None):
        """
        设置API
        :param ctp_api: CTP API实例
        :param platform: 接入平台
        :param env: 运行环境
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
        :param app_context: 应用上下文实例
        :return: MarketDataController实例
        """
        main_logger.info("Main", "Initializing market data API (MD)")

        # 从app_context中获取服务器配置
        conf = app_context.ctp_server[platform][env]

        # 创建行情控制器，使用默认的instrument.yml路径
        ctp_ctr = MarketDataController(
            conf, ctp_api, exchanges=exchanges, app_context=app_context)
        ctp_api.RegisterFront(conf['md_server'])
        return ctp_ctr

    def _start_api(self, ctp_ctr):
        """
        启动API
        :param ctp_ctr: MarketDataController实例
        """
        main_logger.info("Main", "Starting market data API")
        ctp_ctr.start()

    def run(self, platform="SIMNOW", env="simulation_7*24", exchanges="all", app_context=None):
        """
        运行行情数据收集器（market data）
        :param platform: 接入平台，可选 SIMNOW/ZXJT/OPENCTP，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
        :param app_context: 应用上下文实例
        """
        main_logger.info(
            "Main", f"Starting market data client | Platform: {platform} | Environment: {env}")

        try:
            # 使用上下文管理器管理API资源
            with CTPAPIContext(
                api_create_func=mdapi.CThostFtdcMdApi.CreateFtdcMdApi,
                create_args=(STREAM_PATH, IS_PRODUCTION_MODE)
            ) as ctp_api:
                # 设置API
                ctp_ctr = self._setup_api(
                    ctp_api, platform, env, exchanges=exchanges, app_context=app_context)

                # 启动API
                self._start_api(ctp_ctr)

                # 使用上下文管理器管理后台线程
                with BackgroundThreadContext(
                    target=_trading_event_loop,
                    args=(ctp_api,)
                ):
                    # 主线程等待退出
                    main_logger.info(
                        "Main", "Market data client started (Press Ctrl+C to exit)...")
                    wait_for_exit()

                    # 停止控制器
                    if ctp_ctr:
                        ctp_ctr.stop()

                    main_logger.info(
                        "Main", "Stopping market data resources...")
        except KeyboardInterrupt:
            # 确保Ctrl+C能够立即中断并退出
            main_logger.info(
                "Main", "KeyboardInterrupt received, exiting immediately...")
            EXIT_FLAG.set()
        except Exception as e:
            main_logger.error("Main", f"Error occurred in market data: {e}")
            EXIT_FLAG.set()
        finally:
            main_logger.info("Main", "Market data client gracefully exited")
