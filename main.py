# -*- coding: utf-8 -*-
import time
from openctp_ctp import thostmduserapi as mdapi
from openctp_ctp import thosttraderapi as tdapi
from signal_handler import (
    EXIT_FLAG, register_signals,
    run_in_background, wait_for_exit,
    stop_background_thread
)
from config import CONF_LIST, DEFAULT_SUBSCRIBE_INSTRUMENT

# 从controller导入所需类（保持原有路径）
from controller import MarketDataController, TradeController

# ===================== 通用核心逻辑（唯一入口） =====================
def run_ctp_client(platform, env, api_type):
    """
    通用CTP客户端主函数（适配新配置结构）
    :param platform: 平台名称（'ZXJT'/'SIMNOW'）
    :param env: 环境名称（如ZXJT的'verifying'/'simulation'，SIMNOW的'simulation_0'/'simulation_7*24'）
    :param api_type: API类型（'md'=行情，'trade'=交易）
    """
    # 1. 注册信号监听（捕获Ctrl+C）
    register_signals()
    # 2. 加载配置（适配嵌套字典结构）
    try:
        conf = CONF_LIST[platform][env]
    except KeyError as e:
        raise ValueError(f"配置不存在：platform={platform}, env={env}，错误键：{e}") from e

    ctp_api = None

    try:
        # ---------------------- 初始化CTP实例（差异化逻辑） ----------------------
        if api_type == 'md':
            # 行情API初始化
            ctp_api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi()
            ctp_ctr = MarketDataController(conf=conf, api=ctp_api)
            ctp_api.RegisterFront(conf['md_server'])
        elif api_type == 'trade':
            # 交易API初始化（兼容配置中'trade_server'/'trader_server'字段）
            trade_server_key = 'trade_server' if 'trade_server' in conf else 'trader_server'
            ctp_api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi()
            ctp_ctr = TradeController(conf=conf, api=ctp_api)
            ctp_api.RegisterFront(conf[trade_server_key])
            # 交易专属配置：订阅私有/公共流
            ctp_api.SubscribePrivateTopic(0)  # 只传送登录后的流内容
            # ctp_api.SubscribePublicTopic(0)   # 只传送登录后的流内容
        else:
            raise ValueError(f"不支持的API类型：{api_type}，仅支持'md'/'trade'")

        # ---------------------- 公共初始化流程 ----------------------
        # 注册SPI回调
        ctp_api.RegisterSpi(ctp_ctr)
        
        # 交易API专属：补充查询逻辑
        if api_type == 'trade':
            query_trading_info(ctp_api, ctp_ctr, conf)

        # ---------------------- 启动事件循环 ----------------------
        # 后台线程运行CTP事件循环
        ctp_thread = run_in_background(_ctp_event_loop, ctp_api)
        # 主线程等待退出信号
        wait_for_exit()
        # 停止后台线程
        stop_background_thread(ctp_thread)

        print(f"\nCTP {api_type.upper()}客户端（{platform}-{env}）已优雅退出")

    except Exception as e:
        print(f"\nCTP {api_type.upper()}客户端（{platform}-{env}）运行出错：{e}")
        EXIT_FLAG.set()
    finally:
        # 确保API资源释放
        if ctp_api:
            ctp_api.Release()

def _ctp_event_loop(ctp_api):
    """CTP事件循环（内部函数，不对外暴露）"""
    ctp_api.Init()
    while not EXIT_FLAG.is_set():
        time.sleep(0.1)
    ctp_api.Join()
    print(f"CTP API事件循环已停止（{ctp_api.__class__.__name__}）")

# ===================== 交易专属查询逻辑 =====================
def query_trading_info(trade_api, trade_ctr, conf):
    """交易API专属：查询投资者、持仓、账户信息 + 结算单确认"""
    print(f"交易API启动（{conf['broker_id']}-{conf['investor_id']}），当前交易日：{trade_api.GetTradingDay()}")
    
    # # 1. 查询投资者信息
    # investor_qry = tdapi.CThostFtdcQryInvestorField()
    # investor_qry.BrokerID = conf['broker_id']
    # investor_qry.InvestorID = conf['investor_id']
    # v0 = trade_api.ReqQryInvestor(investor_qry, trade_ctr.request_id)
    # print(f"res={v0}, BrokerID={investor_qry.BrokerID}, InvestorID={investor_qry.InvestorID}")
    # time.sleep(1)  # 避免请求过快触发限流
    # trade_api.Join()
    
    # # 2. 查询指定合约持仓（使用默认订阅合约）
    position_qry = tdapi.CThostFtdcQryInvestorPositionField()
    position_qry.BrokerID = conf['broker_id']
    position_qry.InvestorID = conf['investor_id']
    position_qry.InstrumentID = DEFAULT_SUBSCRIBE_INSTRUMENT.decode('utf-8')  # 复用通用配置中的合约
    v1 = trade_api.ReqQryInvestorPosition(position_qry, trade_ctr.request_id)
    print(f"v1 = {v1}")
    time.sleep(1)  # 避免请求过快触发限流
    trade_api.Join()
    
    # # 3. 查询交易账户
    # account_qry = tdapi.CThostFtdcQryTradingAccountField()
    # account_qry.BrokerID = conf['broker_id']
    # account_qry.InvestorID = conf['investor_id']
    # account_qry.BizType = '1'  # 1=普通交易
    # trade_api.ReqQryTradingAccount(account_qry, trade_ctr.request_id)
    # time.sleep(0.1)
    
    # # 4. 结算单确认（交易必备流程）
    # settlement_confirm = tdapi.CThostFtdcSettlementInfoConfirmField()
    # settlement_confirm.BrokerID = conf['broker_id']
    # settlement_confirm.InvestorID = conf['investor_id']
    # trade_api.ReqSettlementInfoConfirm(settlement_confirm, trade_ctr.request_id)

# ===================== 程序唯一入口 =====================
if __name__ == "__main__":
    # ---------------------- 运行配置（按需修改） ----------------------
    # 平台选择：ZXJT / SIMNOW
    PLATFORM = 'SIMNOW'
    # 环境选择：
    #   - ZXJT: verifying / simulation
    #   - SIMNOW: simulation_0 / simulation_1 / simulation_2 / simulation_7*24
    ENV = 'simulation_7*24'
    # API类型：md（行情） / trade（交易）
    API_TYPE = 'trade'

    # 启动CTP客户端
    run_ctp_client(platform=PLATFORM, env=ENV, api_type=API_TYPE)