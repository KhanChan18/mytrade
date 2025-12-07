# -*- coding: utf-8 -*-
"""最终整合版：原入口逻辑 + td_demo的业务流程（接入日志类 + fire命令行支持）"""
# 仅导入必要模块（无重复）
import time
import fire
from openctp_ctp import thostmduserapi as mdapi
from openctp_ctp import thosttraderapi as tdapi

# 自定义模块（仅导入一次）
from signal_handler import (
    EXIT_FLAG, register_signals,
    run_in_background, wait_for_exit,
    stop_background_thread
)
from config import CONF_LIST, DEFAULT_INSTRUMENT_STR, ORDER_PARAMS_DEFAULT, get_config, LOG_CONFIG
from controller import MarketDataController, TradeController
from logger import CTPLogger

# 全局日志实例（主流程日志）
main_logger = CTPLogger(
    log_file=LOG_CONFIG["log_file"],
    log_level=LOG_CONFIG["log_level"]
)

class CTPClient:
    """
    CTP客户端命令行工具
    支持快速测试market data（行情）和trade（交易）功能
    """
    
    def __init__(self):
        """初始化：注册信号监听（全局）"""
        register_signals()

    def run(self, platform="SIMNOW", env="simulation_7*24", api_type="trade"):
        """
        启动CTP客户端（核心函数，兼容原有逻辑）
        :param platform: 接入平台，可选 SIMNOW/ZXJT，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        :param api_type: 功能类型，可选 md（行情）/trade（交易），默认 trade
        """
        main_logger.info("Main", f"启动{api_type.upper()}客户端 | 平台: {platform} | 环境: {env}")
        
        # 2. 加载配置
        try:
            conf = get_config(platform, env)
        except ValueError as e:
            main_logger.error("Main", f"加载配置失败: {e}")
            EXIT_FLAG.set()
            return

        ctp_api = None
        ctp_ctr = None

        try:
            # ---------------------- 初始化API和控制器 ----------------------
            if api_type == 'md':
                # 行情初始化（market data）
                main_logger.info("Main", "初始化行情API（MD）")
                ctp_api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi()
                ctp_ctr = MarketDataController(conf, ctp_api)
                ctp_api.RegisterFront(conf['md_server'])
            elif api_type == 'trade':
                # 交易初始化（trade）
                main_logger.info("Main", "初始化交易API（Trade）")
                ctp_api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi()
                ctp_ctr = TradeController(conf, ctp_api)
                # 兼容SIMNOW的trader_server和ZXJT的trade_server
                trade_server_key = 'trader_server' if 'trader_server' in conf else 'trade_server'
                ctp_api.RegisterFront(conf[trade_server_key])
                # 交易专属配置（来自td_demo）
                ctp_api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
                ctp_api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)
            else:
                raise ValueError(f"不支持的API类型: {api_type}，仅支持 md（行情）/trade（交易）")

            # ---------------------- 公共初始化 ----------------------
            ctp_api.RegisterSpi(ctp_ctr)
            ctp_ctr.start()  # 启动API

            # ---------------------- 交易业务逻辑（来自td_demo） ----------------------
            if api_type == 'trade':
                # 等待登录完成（信号量同步）
                main_logger.info("Main", "等待登录完成...")
                try:
                    # 等待认证响应（10秒超时）
                    if not ctp_ctr.semaphore.acquire(timeout=10):
                        raise TimeoutError("认证超时")
                    # 等待登录响应（10秒超时）
                    if not ctp_ctr.semaphore.acquire(timeout=10):
                        raise TimeoutError("登录超时")
                except TimeoutError as e:
                    main_logger.error("Main", f"登录失败: {e}")
                    EXIT_FLAG.set()
                    return

                # 登录成功后执行业务操作（td_demo的查询/下单）
                if ctp_ctr.login:
                    main_logger.info("Main", "登录成功，开始执行业务操作")
                    # 1. 查询合约
                    ctp_ctr.QryInstrument(exchangeid="DCE", instrumentid=DEFAULT_INSTRUMENT_STR)
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
            ctp_thread = run_in_background(_ctp_event_loop, ctp_api)
            # 主线程等待退出
            main_logger.info("Main", f"{api_type.upper()}客户端已启动（按Ctrl+C退出）...")
            wait_for_exit()

            # ---------------------- 停止资源 ----------------------
            stop_background_thread(ctp_thread)
            ctp_ctr.stop()
            main_logger.info("Main", f"{api_type.upper()}客户端已优雅退出")

        except Exception as e:
            main_logger.error("Main", f"运行出错: {e}")
            EXIT_FLAG.set()
        finally:
            if ctp_api:
                ctp_api.Release()

    def market_data_test(self, platform="SIMNOW", env="simulation_7*24"):
        """
        快速测试行情（market data）功能（快捷命令）
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        """
        self.run(platform=platform, env=env, api_type="md")

    def trade_test(self, platform="SIMNOW", env="simulation_7*24"):
        """
        快速测试交易（trade）功能（快捷命令）
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        """
        self.run(platform=platform, env=env, api_type="trade")

def _ctp_event_loop(ctp_api):
    """CTP事件循环"""
    while not EXIT_FLAG.is_set():
        time.sleep(0.1)
    ctp_api.Join()
    main_logger.debug("Main", "CTP事件循环已停止")

# ===================== 程序入口（支持命令行 + 直接运行） =====================
if __name__ == "__main__":
    # 方式1：通过fire库暴露命令行接口
    fire.Fire(CTPClient)
    
    # 方式2：保留原有直接运行逻辑（如需默认运行，取消以下注释）
    # client = CTPClient()
    # client.run(platform='SIMNOW', env='simulation_7*24', api_type='trade')