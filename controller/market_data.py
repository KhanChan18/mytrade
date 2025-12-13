# -*- coding: utf-8 -*-
"""行情控制器（MarketDataController）"""
import yaml
import os
from openctp_ctp import thostmduserapi as mdapi
from . import BaseController
from .tools import generate_contract_dict
from .callbacks import MarketDataSpi
from model.market_data import MarketData
from utils.misc import set_req_fields
from db import create_data_collector
from config import DB_TYPE, BUFFER_SIZE, DB_PATH
from utils.logger import main_logger

# 生成合约列表
contract_dict = generate_contract_dict(os.path.join(os.path.dirname(__file__), 'instrument.yml'))

# ===================== 行情控制器 =====================
class MarketDataController(BaseController):
    """行情控制器"""
    def __init__(self, conf, api):
        super().__init__(conf, api)
        # 初始化数据收集器
        self.data_collector = create_data_collector(
            db_type=DB_TYPE,
            buffer_size=BUFFER_SIZE,
            db_path=DB_PATH
        )
        # 创建并注册行情数据SPI回调
        self.spi = MarketDataSpi(self)
        self.api.RegisterSpi(self.spi)
        # 订阅相关计数器
        self.subscribed_count = 0
        self.total_to_subscribe = 0

    def login(self):
        """发起行情登录请求"""
        res = self.send_request(
            "ReqUserLogin",
            {
                "BrokerID": self.conf['broker_id'],
                "UserID": self.conf['investor_id'],
                "Password": self.conf['password']
            },
            "ReqUserLogin"
        )

    def subscribe_market_data(self):
        """订阅行情数据"""
        instrument_list = contract_dict['all']
        instrument_list = [inst.encode("utf-8") for inst in instrument_list]
        self.total_to_subscribe = len(instrument_list)
        main_logger.info("MDController", f"Subscribing to {self.total_to_subscribe} market data contracts")
        self.api.SubscribeMarketData(instrument_list, len(instrument_list))

    def process_market_data(self, market_data_dict):
        """处理行情数据"""
        # 将行情数据添加到数据收集器
        self.data_collector.add_data(market_data_dict)