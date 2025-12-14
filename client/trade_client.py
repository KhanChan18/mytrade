# -*- coding: utf-8 -*-
"""交易客户端"""
import time
from openctp_ctp import thosttraderapi as tdapi

# 自定义模块
from utils.signal import (EXIT_FLAG, register_signals, wait_for_exit)
from utils.context import CTPAPIContext, BackgroundThreadContext, AppContext
from config import (STREAM_PATH, IS_PRODUCTION_MODE, get_server_config)
from controller import TradeController
from utils.logger import main_logger

# 交易相关配置
DEFAULT_INSTRUMENT_STR = "rb2601"  # 默认合约代码
ORDER_PARAMS_DEFAULT = {
    "ExchangeID": "SHFE",
    "InstrumentID": DEFAULT_INSTRUMENT_STR,
    "Direction": tdapi.THOST_FTDC_D_Buy,
    "CombOffsetFlag": tdapi.THOST_FTDC_OF_Open,
    "OrderPriceType": tdapi.THOST_FTDC_OPT_LimitPrice,
    "LimitPrice": 13633,
    "VolumeTotalOriginal": 1,
    "TimeCondition": tdapi.THOST_FTDC_TC_GFD,
    "VolumeCondition": tdapi.THOST_FTDC_VC_AV,
    "MinVolume": 1,
    "IsAutoSpeed": 0,
    "IsSwapOrder": 0,
    "ForceCloseReason": tdapi.THOST_FTDC_FCC_NotForceClose,
    "StopPrice": 13300,
}


def _trading_event_loop(ctp_api):
    """交易事件循环"""
    try:
        while not EXIT_FLAG.is_set():
            # 使用更短的轮询间隔，提高响应速度
            time.sleep(0.01)
    finally:
        ctp_api.Join()
        main_logger.debug("Main", "Trading event loop stopped")


class TradeClient:
    """
    交易客户端
    负责交易处理逻辑
    """

    def __init__(self):
        """初始化：注册信号监听"""
        register_signals()

    def _setup_api(self, ctp_api, app_context):
        """
        设置API
        :param ctp_api: CTP API实例
        :param app_context: 应用上下文实例
        :param platform: 接入平台
        :param env: 运行环境
        :return: TradeController实例
        """
        main_logger.info("Main", "Initializing trade API (Trade)")
        ctp_ctr = TradeController(app_context.ctp_server, ctp_api)
        ctp_api.RegisterFront(app_context.ctp_server["trade_server"])
        ctp_api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
        ctp_api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)
        return ctp_ctr

    def _start_api(self, ctp_ctr):
        """
        启动API
        :param ctp_ctr: TradeController实例
        """
        main_logger.info("Main", "Starting trade API")
        ctp_ctr.start()

    def _login(self, ctp_ctr):
        """
        等待登录完成
        :param ctp_ctr: TradeController实例
        :raises TimeoutError: 登录超时
        """
        main_logger.info("Main", "Waiting for login to complete...")
        # 等待认证响应（10秒超时）
        if not ctp_ctr.semaphore.acquire(timeout=10):
            raise TimeoutError("认证超时")
        # 等待登录响应（10秒超时）
        if not ctp_ctr.semaphore.acquire(timeout=10):
            raise TimeoutError("登录超时")

    def _execute_business_operations(self, ctp_ctr):
        """
        执行业务操作
        :param ctp_ctr: TradeController实例
        """
        if ctp_ctr.is_logged_in:
            main_logger.info("Main",
                             "Login successful, starting business operations")
            # 1. 查询合约
            ctp_ctr.QryInstrument(exchangeid="SHFE",
                                  instrumentid=DEFAULT_INSTRUMENT_STR)
            ctp_ctr.semaphore.acquire(timeout=5)
            time.sleep(0.5)

            # 2. 查询持仓
            ctp_ctr.QryPosition(instrumentid=DEFAULT_INSTRUMENT_STR)
            ctp_ctr.semaphore.acquire(timeout=5)
            time.sleep(0.5)

            # 3. 下单
            ctp_ctr.OrderInsert(ORDER_PARAMS_DEFAULT)
            ctp_ctr.semaphore.acquire(timeout=5)
            time.sleep(0.5)

    def run(self, platform="SIMNOW", env="simulation_7*24", app_context=None):
        """
        运行交易控制器（trade）
        :param platform: 接入平台，可选 SIMNOW/ZXJT/OPENCTP，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        :param app_context: 应用上下文实例
        """
        main_logger.info(
            "Main",
            f"Starting trade client | Platform: {platform} | Environment: {env}"
        )

        try:
            # 使用上下文管理器管理API资源
            with CTPAPIContext(
                api_create_func=tdapi.CThostFtdcTraderApi.
                CreateFtdcTraderApi,
                create_args=(STREAM_PATH, IS_PRODUCTION_MODE)
            ) as ctp_api:
                # 设置API
                ctp_ctr = self._setup_api(ctp_api, app_context)
                # 启动API
                self._start_api(ctp_ctr)
                try:
                    self._login(ctp_ctr)
                    self._execute_business_operations(ctp_ctr)
                except TimeoutError as e:
                    main_logger.error("Main", f"Login failed: {e}")
                    EXIT_FLAG.set()
                    return

                # 使用上下文管理器管理后台线程
                with BackgroundThreadContext(target=_trading_event_loop,
                                             args=(ctp_api, )):
                    # 主线程等待退出
                    main_logger.info(
                        "Main",
                        "Trade client started (Press Ctrl+C to exit)...")
                    wait_for_exit()

                    # 停止控制器
                    if ctp_ctr:
                        ctp_ctr.stop()

                    main_logger.info("Main", "Stopping trade resources...")
        except KeyboardInterrupt:
            # 确保Ctrl+C能够立即中断并退出
            main_logger.info(
                "Main", "KeyboardInterrupt received, exiting immediately...")
            EXIT_FLAG.set()
        except Exception as e:
            main_logger.error("Main", f"Error occurred in trade: {e}")
            EXIT_FLAG.set()
        finally:
            main_logger.info("Main", "Trade client gracefully exited")
