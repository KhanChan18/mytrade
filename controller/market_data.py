# -*- coding: utf-8 -*-
"""行情控制器（MarketDataController）"""
import yaml
import os
from openctp_ctp import thostmduserapi as mdapi
from . import BaseController
from .utils import generate_contract_dict
from signal_handler import EXIT_FLAG
from utils import set_req_fields

# 生成合约列表
contract_dict = generate_contract_dict(os.path.join(os.path.dirname(__file__), 'instrument.yml'))

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
        instrument_list = contract_dict['all']
        instrument_list = [inst.encode("utf-8") for inst in instrument_list]
        self.api.SubscribeMarketData(instrument_list, len(instrument_list))
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
        
        # 利用日志类的print_error方法
        if self.logger.print_error("MDController_Subscribe", pRspInfo):
            self.logger.release_semaphore(bIsLast)
            return
        
        # 处理pSpecificInstrument为None的情况
        inst_id = pSpecificInstrument.InstrumentID if pSpecificInstrument else "未知合约"
        self.logger.info("MDController", f"订阅成功: {inst_id}")
        self.logger.release_semaphore(bIsLast)