# -*- coding: utf-8 -*-
"""行情控制器（MarketDataController）"""
import yaml
import os
from openctp_ctp import thostmduserapi as mdapi
from . import BaseController
from .utils import generate_contract_dict
from signal_handler import EXIT_FLAG
from utils import set_req_fields
from data_collection import create_data_collector
from config import DB_TYPE, BUFFER_SIZE, DB_PATH

# 生成合约列表
contract_dict = generate_contract_dict(os.path.join(os.path.dirname(__file__), 'instrument.yml'))

# ===================== 行情控制器（仅保留差异化，接入日志类） =====================
class MarketDataController(BaseController, mdapi.CThostFtdcMdSpi):
    """行情控制器"""
    def __init__(self, conf, api):
        mdapi.CThostFtdcMdSpi.__init__(self)
        super().__init__(conf, api)
        # 初始化数据收集器
        self.data_collector = create_data_collector(
            db_type=DB_TYPE,
            buffer_size=BUFFER_SIZE,
            db_path=DB_PATH
        )

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
        # 将行情对象转换为字典
        market_data_dict = {
            "InstrumentID": pDepthMarketData.InstrumentID,
            "TradingDay": getattr(pDepthMarketData, "TradingDay", ""),
            "ActionDay": getattr(pDepthMarketData, "ActionDay", ""),
            "UpdateTime": getattr(pDepthMarketData, "UpdateTime", ""),
            "UpdateMillisec": getattr(pDepthMarketData, "UpdateMillisec", 0),
            "LastPrice": getattr(pDepthMarketData, "LastPrice", 0),
            "Volume": getattr(pDepthMarketData, "Volume", 0),
            "PreSettlementPrice": getattr(pDepthMarketData, "PreSettlementPrice", 0),
            "PreClosePrice": getattr(pDepthMarketData, "PreClosePrice", 0),
            "PreOpenInterest": getattr(pDepthMarketData, "PreOpenInterest", 0),
            "OpenPrice": getattr(pDepthMarketData, "OpenPrice", 0),
            "HighestPrice": getattr(pDepthMarketData, "HighestPrice", 0),
            "LowestPrice": getattr(pDepthMarketData, "LowestPrice", 0),
            "LimitUpPrice": getattr(pDepthMarketData, "LimitUpPrice", 0),
            "LimitDownPrice": getattr(pDepthMarketData, "LimitDownPrice", 0),
            "OpenInterest": getattr(pDepthMarketData, "OpenInterest", 0),
            "Turnover": getattr(pDepthMarketData, "Turnover", 0),
            "AveragePrice": getattr(pDepthMarketData, "AveragePrice", 0),
            # 买卖盘口数据
            "BidPrice1": getattr(pDepthMarketData, "BidPrice1", 0),
            "BidVolume1": getattr(pDepthMarketData, "BidVolume1", 0),
            "AskPrice1": getattr(pDepthMarketData, "AskPrice1", 0),
            "AskVolume1": getattr(pDepthMarketData, "AskVolume1", 0),
            "BidPrice2": getattr(pDepthMarketData, "BidPrice2", 0),
            "BidVolume2": getattr(pDepthMarketData, "BidVolume2", 0),
            "AskPrice2": getattr(pDepthMarketData, "AskPrice2", 0),
            "AskVolume2": getattr(pDepthMarketData, "AskVolume2", 0),
            "BidPrice3": getattr(pDepthMarketData, "BidPrice3", 0),
            "BidVolume3": getattr(pDepthMarketData, "BidVolume3", 0),
            "AskPrice3": getattr(pDepthMarketData, "AskPrice3", 0),
            "AskVolume3": getattr(pDepthMarketData, "AskVolume3", 0),
            "BidPrice4": getattr(pDepthMarketData, "BidPrice4", 0),
            "BidVolume4": getattr(pDepthMarketData, "BidVolume4", 0),
            "AskPrice4": getattr(pDepthMarketData, "AskPrice4", 0),
            "AskVolume4": getattr(pDepthMarketData, "AskVolume4", 0),
            "BidPrice5": getattr(pDepthMarketData, "BidPrice5", 0),
            "BidVolume5": getattr(pDepthMarketData, "BidVolume5", 0),
            "AskPrice5": getattr(pDepthMarketData, "AskPrice5", 0),
            "AskVolume5": getattr(pDepthMarketData, "AskVolume5", 0),
        }

        self.logger.info(
            "MDController_MarketData",
            f"{pDepthMarketData.InstrumentID} 最新价: {pDepthMarketData.LastPrice} 成交量: {pDepthMarketData.Volume}"
        )
        
        # 将行情数据添加到数据收集器
        self.data_collector.add_data(market_data_dict)

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