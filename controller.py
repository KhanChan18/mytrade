# -*- coding: utf-8 -*-
"""整合BaseController+行情/交易控制器+td_demo核心逻辑（接入日志类）"""
# 仅导入一次核心模块
from openctp_ctp import thostmduserapi as mdapi
from openctp_ctp import thosttraderapi as tdapi
import threading
from signal_handler import EXIT_FLAG
from utils import set_req_fields
from config import INSTRUMENT_LIST, LOG_CONFIG
from logger import CTPLogger

# ===================== 公共父类（整合td_demo核心逻辑 + 日志类） =====================
class BaseController:
    """公共父类：整合信号量、优雅退出、日志打印（基于CTPLogger）"""
    def __init__(self, conf=None, api=None):
        self.conf = conf
        self.api = api
        self._request_id = 100
        self.login = False
        self.is_running = False
        self.semaphore = threading.Semaphore(0)  # td_demo的信号量
        self.OrderRef = 0  # td_demo的报单引用
        
        # 初始化日志类（接入配置中的日志参数）
        self.logger = CTPLogger(
            log_file=LOG_CONFIG["log_file"],
            log_level=LOG_CONFIG["log_level"]
        )
        self.logger.set_semaphore(self.semaphore)  # 设置信号量

    @property
    def request_id(self):
        """自增请求ID"""
        self._request_id += 1
        return self._request_id

    def start(self):
        """启动API（替代td_demo的Run）"""
        self.is_running = True
        self.logger.info("BaseController", "启动CTP API")
        self.api.Init()

    def stop(self):
        """优雅停止（来自td_demo）"""
        if not self.is_running:
            return
        self.logger.info("BaseController", "开始停止CTP API...")
        self.is_running = False
        EXIT_FLAG.set()
        try:
            self.api.RegisterFront("")
            self.api.Release()
            self.logger.info("BaseController", "CTP API已安全释放")
        except Exception as e:
            self.logger.error("BaseController", f"释放API失败: {e}")

    # 公共回调（抽离重复逻辑，处理pRspInfo为None的情况 + 日志）
    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """公共错误回调"""
        if pRspInfo is None:
            self.logger.error("OnRspError", f"RequestID={nRequestID}, pRspInfo为None")
        else:
            err_msg = pRspInfo.ErrorMsg.encode('gbk', 'ignore') if pRspInfo.ErrorMsg else 'None'
            self.logger.error("OnRspError", f"RequestID={nRequestID}, ErrorID={pRspInfo.ErrorID}, Msg={err_msg}")
        self.logger.release_semaphore(bIsLast)

    def OnHeartBeatWarning(self, nTimeLapse):
        """公共心跳警告"""
        self.logger.debug("OnHeartBeatWarning", f"心跳超时警告: {nTimeLapse}秒")

    def OnFrontDisconnected(self, nReason):
        """公共断开回调"""
        self.logger.error("OnFrontDisconnected", f"前置机断开，原因: {nReason}")
        EXIT_FLAG.set()

# ===================== 行情控制器（仅保留差异化，接入日志类） =====================
class MarketDataController(BaseController, mdapi.CThostFtdcMdSpi):
    """行情控制器"""
    def __init__(self, conf, api):
        mdapi.CThostFtdcMdSpi.__init__(self)
        super().__init__(conf, api)

    def OnFrontConnected(self):
        """行情连接成功"""
        self.logger.info("MDController", "前置机连接成功，开始登录")
        req = mdapi.CThostFtdcReqUserLoginField()
        set_req_fields(req, {
            "BrokerID": self.conf['broker_id'],
            "UserID": self.conf['investor_id'],
            "Password": self.conf['password']
        })
        res = self.api.ReqUserLogin(req, self.request_id)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """行情登录响应"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("MDController", f"登录失败: pRspInfo为None")
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error方法
        if self.logger.print_error("MDController_Login", pRspInfo):
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        self.login = True
        trading_day = pRspUserLogin.TradingDay if pRspUserLogin else '未知'
        self.logger.info("MDController", f"登录成功，交易日: {trading_day}")
        new_request_id = self.request_id
        self.api.SubscribeMarketData(INSTRUMENT_LIST, len(INSTRUMENT_LIST))
        self.logger.release_semaphore(bIsLast)

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """行情推送"""
        if pDepthMarketData is None:
            self.logger.error("MDController", "行情推送: pDepthMarketData为None")
            return
        self.logger.info(
            "MDController_MarketData",
            f"{pDepthMarketData.InstrumentID} 最新价: {pDepthMarketData.LastPrice} 成交量: {pDepthMarketData.Volume}"
        )

    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """行情订阅响应"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("MDController", f"订阅失败: pRspInfo为None")
            self.logger.release_semaphore(bIsLast)
            return
        
        # 处理pSpecificInstrument为None的情况
        if pSpecificInstrument is None:
            inst_id = "未知合约"
        
        # 利用日志类的print_error方法
        if self.logger.print_error("MDController_Subscribe", pRspInfo):
            self.logger.release_semaphore(bIsLast)
            return
        
        self.logger.info("MDController", f"订阅成功: {pSpecificInstrument.InstrumentID}")
        self.logger.release_semaphore(bIsLast)

# ===================== 交易控制器（整合td_demo核心逻辑 + 日志类） =====================
class TradeController(BaseController, tdapi.CThostFtdcTraderSpi):
    """交易控制器：整合td_demo的认证/登录/下单/查询逻辑 + 日志类"""
    def __init__(self, conf, api):
        tdapi.CThostFtdcTraderSpi.__init__(self)
        super().__init__(conf, api)
        self.TradingDay = ""  # td_demo的交易日

    def OnFrontConnected(self):
        """交易连接成功（认证逻辑来自td_demo）"""
        self.logger.info("TradeController", "前置机连接成功，开始认证")
        req = tdapi.CThostFtdcReqAuthenticateField()
        set_req_fields(req, {
            "BrokerID": self.conf['broker_id'],
            "UserID": self.conf['investor_id'],
            "AppID": self.conf['app_id'],
            "AuthCode": self.conf['auth_code']
        })
        self.api.ReqAuthenticate(req, self.request_id)

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """交易认证响应（来自td_demo）"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("TradeController", f"认证失败: pRspInfo为None")
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error方法
        if self.logger.print_error("TradeController_Auth", pRspInfo):
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        self.logger.info("TradeController", "认证成功，开始登录")
        req = tdapi.CThostFtdcReqUserLoginField()
        set_req_fields(req, {
            "BrokerID": self.conf['broker_id'],
            "UserID": self.conf['investor_id'],
            "Password": self.conf['password']
        })
        self.api.ReqUserLogin(req, self.request_id)
        self.logger.release_semaphore(bIsLast)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """交易登录响应（来自td_demo）"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("TradeController", f"登录失败: pRspInfo为None")
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error方法
        if self.logger.print_error("TradeController_Login", pRspInfo):
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        self.login = True
        self.TradingDay = pRspUserLogin.TradingDay if (pRspUserLogin and pRspUserLogin.TradingDay) else ""
        self.OrderRef = 1
        max_order_ref = pRspUserLogin.MaxOrderRef if (pRspUserLogin and pRspUserLogin.MaxOrderRef) else "未知"
        self.logger.info("TradeController", f"登录成功 | 交易日: {self.TradingDay} | 最大报单引用: {max_order_ref}")
        self.logger.release_semaphore(bIsLast)

    # ========== td_demo的业务方法（查询/下单 + 日志） ==========
    def QryInstrument(self, exchangeid="", instrumentid=""):
        """查询合约（来自td_demo）"""
        self.logger.info("TradeController_Qry", f"查询合约 | 交易所: {exchangeid} | 合约: {instrumentid}")
        req = tdapi.CThostFtdcQryInstrumentField()
        set_req_fields(req, {
            "ExchangeID": exchangeid,
            "InstrumentID": instrumentid
        })
        self.api.ReqQryInstrument(req, self.request_id)

    def QryPosition(self, instrumentid=""):
        """查询持仓（来自td_demo）"""
        self.logger.info("TradeController_Qry", f"查询持仓 | 合约: {instrumentid}")
        req = tdapi.CThostFtdcQryInvestorPositionField()
        set_req_fields(req, {
            "BrokerID": self.conf['broker_id'],
            "InvestorID": self.conf['investor_id'],
            "InstrumentID": instrumentid
        })
        self.api.ReqQryInvestorPosition(req, self.request_id)

    def OrderInsert(self, order_params):
        """下单（来自td_demo）"""
        self.logger.info("TradeController_Order", f"开始下单 | 参数: {order_params}")
        req = tdapi.CThostFtdcInputOrderField()
        # 基础字段（来自td_demo）
        base_fields = {
            "BrokerID": self.conf['broker_id'],
            "InvestorID": self.conf['investor_id'],
            "CombHedgeFlag": tdapi.THOST_FTDC_HF_Speculation,
            "ForceCloseReason": tdapi.THOST_FTDC_FCC_NotForceClose,
            "ContingentCondition": tdapi.THOST_FTDC_CC_Immediately,
            "OrderRef": str(self.OrderRef)
        }
        # 合并字段
        all_fields = {**base_fields, **order_params}
        set_req_fields(req, all_fields)
        # 发送下单请求
        ret = self.api.ReqOrderInsert(req, self.request_id)
        self.logger.info("TradeController_Order", f"下单请求已发送 | 报单结果: {ret}")
        self.OrderRef += 1

    # ========== td_demo的回调方法（接入日志类） ==========
    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """查询合约响应"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("TradeController_Qry", f"查询合约响应: pRspInfo为None")
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error和print_object方法
        if self.logger.print_error("TradeController_QryInstrument", pRspInfo):
            self.logger.release_semaphore(bIsLast)
            return
        
        if pInstrument:
            self.logger.print_object("TradeController_QryInstrument", pInstrument, "Instrument")
        self.logger.release_semaphore(bIsLast)

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """查询持仓响应"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("TradeController_Qry", f"查询持仓响应: pRspInfo为None")
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error和print_object方法
        if self.logger.print_error("TradeController_QryPosition", pRspInfo):
            self.logger.release_semaphore(bIsLast)
            return
        
        if pInvestorPosition:
            self.logger.print_object("TradeController_QryPosition", pInvestorPosition, "Position")
        self.logger.release_semaphore(bIsLast)

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """下单响应"""
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            self.logger.error("TradeController_Order", f"下单响应: pRspInfo为None")
            self.logger.release_semaphore(bIsLast)
            return
        
        # 利用日志类的print_error方法
        if self.logger.print_error("TradeController_OrderInsert", pRspInfo):
            self.logger.release_semaphore(bIsLast)
            return
        
        order_ref = pInputOrder.OrderRef if (pInputOrder and pInputOrder.OrderRef) else "未知"
        self.logger.info("TradeController_Order", f"下单请求已受理 | 报单引用: {order_ref}")
        self.logger.release_semaphore(bIsLast)

    def OnRtnOrder(self, pOrder):
        """订单回报"""
        if pOrder is None:
            self.logger.error("TradeController_Rtn", "订单回报: pOrder为None")
            return
        # 利用日志类的print_object方法（使用Order模板）
        self.logger.print_object("TradeController_RtnOrder", pOrder, "Order")

    def OnRtnTrade(self, pTrade):
        """成交回报"""
        if pTrade is None:
            self.logger.error("TradeController_Rtn", "成交回报: pTrade为None")
            return
        # 利用日志类的print_object方法（使用Trade模板）
        self.logger.print_object("TradeController_RtnTrade", pTrade, "Trade")
