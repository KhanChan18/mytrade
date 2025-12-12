# -*- coding: utf-8 -*-
"""交易控制器（TradeController）"""
from openctp_ctp import thosttraderapi as tdapi
from . import BaseController
from signal_handler import EXIT_FLAG
from utils import set_req_fields


class TradeController(BaseController, tdapi.CThostFtdcTraderSpi):
    """交易控制器"""
    def __init__(self, conf, api):
        tdapi.CThostFtdcTraderSpi.__init__(self)
        super().__init__(conf, api)

    def OnFrontConnected(self):
        """交易前置机连接成功"""
        self.logger.info("TradeController", "交易前置机连接成功，开始登录")
        req = tdapi.CThostFtdcReqUserLoginField()
        set_req_fields(req, {
            "BrokerID": self.conf['broker_id'],
            "UserID": self.conf['investor_id'],
            "Password": self.conf['password']
        })
        res = self.api.ReqUserLogin(req, self.request_id)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """交易登录响应"""
        if pRspInfo is None:
            self.logger.error("TradeController", f"登录失败: pRspInfo为None")
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        if self.logger.print_error("TradeController_Login", pRspInfo):
            EXIT_FLAG.set()
            self.logger.release_semaphore(bIsLast)
            return
        
        self.login = True
        trading_day = pRspUserLogin.TradingDay if pRspUserLogin else '未知'
        self.logger.info("TradeController", f"登录成功，交易日: {trading_day}")
        
        # 登录成功后可以执行其他操作，如查询投资者持仓、资金等
        self.logger.release_semaphore(bIsLast)
