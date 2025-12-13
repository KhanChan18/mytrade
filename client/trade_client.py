# -*- coding: utf-8 -*-
"""交易客户端"""
import time
from openctp_ctp import thosttraderapi as tdapi

# 自定义模块
from utils.signal import (
    EXIT_FLAG, register_signals,
    run_in_background, wait_for_exit,
    stop_background_thread, stop_all_background_threads
)
from config import (
    STREAM_PATH, IS_PRODUCTION_MODE, get_server_config
)
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

    def run(self, platform="SIMNOW", env="simulation_7*24"):
        """
        运行交易控制器（trade）
        :param platform: 接入平台，可选 SIMNOW/ZXJT/OPENCTP，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        """
        main_logger.info("Main", f"Starting trade client | Platform: {platform} | Environment: {env}")
        
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
            # ---------------------- 初始化交易API和控制器 ----------------------
            main_logger.info("Main", "Initializing trade API (Trade)")
            ctp_api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi(STREAM_PATH, IS_PRODUCTION_MODE)
            ctp_ctr = TradeController(conf, ctp_api)
            # 兼容SIMNOW的trader_server和ZXJT的trade_server
            trade_server_key = 'trader_server' if 'trader_server' in conf else 'trade_server'
            ctp_api.RegisterFront(conf[trade_server_key])
            # 交易专属配置（来自td_demo）
            ctp_api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
            ctp_api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)

            # ---------------------- 启动API ----------------------
            ctp_ctr.start()  # 启动API

            # ---------------------- 交易业务逻辑（来自td_demo） ----------------------
            # 等待登录完成（信号量同步）
            main_logger.info("Main", "Waiting for login to complete...")
            try:
                # 等待认证响应（10秒超时）
                if not ctp_ctr.semaphore.acquire(timeout=10):
                    raise TimeoutError("认证超时")
                # 等待登录响应（10秒超时）
                if not ctp_ctr.semaphore.acquire(timeout=10):
                    raise TimeoutError("登录超时")
            except TimeoutError as e:
                main_logger.error("Main", f"Login failed: {e}")
                EXIT_FLAG.set()
                return

            # 登录成功后执行业务操作（td_demo的查询/下单）
            if ctp_ctr.is_logged_in:
                main_logger.info("Main", "Login successful, starting business operations")
                # 1. 查询合约
                ctp_ctr.QryInstrument(exchangeid="SHFE", instrumentid=DEFAULT_INSTRUMENT_STR)
                ctp_ctr.semaphore.acquire(timeout=5)
                time.sleep(0.5)

                # 2. 查询持仓
                ctp_ctr.QryPosition(instrumentid=DEFAULT_INSTRUMENT_STR)
                ctp_ctr.semaphore.acquire(timeout=5)
                time.sleep(0.5)

                # 3. 下单（来自td_demo）
                ctp_ctr.OrderInsert(ORDER_PARAMS_DEFAULT)
                ctp_ctr.semaphore.acquire(timeout=5)
                time.sleep(0.5)

            # ---------------------- 启动事件循环 ----------------------
            # 后台运行事件循环
            ctp_thread = run_in_background(_trading_event_loop, ctp_api)
            # 主线程等待退出
            main_logger.info("Main", "Trade client started (Press Ctrl+C to exit)...")
            wait_for_exit()

            # ---------------------- 停止资源 ----------------------
            main_logger.info("Main", "Stopping trade resources...")
        except KeyboardInterrupt:
            # 确保Ctrl+C能够立即中断并退出
            main_logger.info("Main", "KeyboardInterrupt received, exiting immediately...")
            EXIT_FLAG.set()
        except Exception as e:
            main_logger.error("Main", f"Error occurred in trade: {e}")
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
            main_logger.info("Main", "Trade client gracefully exited")
