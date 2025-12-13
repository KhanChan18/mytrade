# -*- coding: utf-8 -*-
"""行情数据客户端"""
import time
from openctp_ctp import thostmduserapi as mdapi

# 自定义模块
from utils.signal import (
    EXIT_FLAG, register_signals,
    run_in_background, wait_for_exit,
    stop_background_thread, stop_all_background_threads
)
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

    def run(self, platform="SIMNOW", env="simulation_7*24"):
        """
        运行行情数据收集器（market data）
        :param platform: 接入平台，可选 SIMNOW/ZXJT/OPENCTP，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        """
        main_logger.info("Main", f"Starting market data client | Platform: {platform} | Environment: {env}")
        
        # 加载配置
        try:
            conf = get_server_config(platform, env)
        except ValueError as e:
            main_logger.error("Main", f"Failed to load configuration: {e}")
            EXIT_FLAG.set()
            return
        
        ctp_api = None
        ctp_ctr = None
        ctp_thread = None
        
        try:
            # ---------------------- 初始化行情API和控制器 ----------------------
            main_logger.info("Main", "Initializing market data API (MD)")
            ctp_api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi(STREAM_PATH, IS_PRODUCTION_MODE)
            ctp_ctr = MarketDataController(conf, ctp_api)
            ctp_api.RegisterFront(conf['md_server'])

            # ---------------------- 启动API ----------------------
            ctp_ctr.start()  # 启动API

            # ---------------------- 启动事件循环 ----------------------
            # 后台运行事件循环
            ctp_thread = run_in_background(_trading_event_loop, ctp_api)
            # 主线程等待退出
            main_logger.info("Main", "Market data client started (Press Ctrl+C to exit)...")
            wait_for_exit()

            # ---------------------- 停止资源 ----------------------
            main_logger.info("Main", "Stopping market data resources...")
        except KeyboardInterrupt:
            # 确保Ctrl+C能够立即中断并退出
            main_logger.info("Main", "KeyboardInterrupt received, exiting immediately...")
            EXIT_FLAG.set()
        except Exception as e:
            main_logger.error("Main", f"Error occurred in market data: {e}")
            EXIT_FLAG.set()
        finally:
            # 确保无论发生什么情况都能清理资源
            if ctp_thread:
                stop_background_thread(ctp_thread)
            if ctp_ctr:
                ctp_ctr.stop()
            if ctp_api:
                ctp_api.Release()
            # 停止所有后台线程
            stop_all_background_threads()
            main_logger.info("Main", "Market data client gracefully exited")
