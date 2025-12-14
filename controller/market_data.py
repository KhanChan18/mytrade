# -*- coding: utf-8 -*-
"""行情控制器（MarketDataController）"""
import yaml
import os
from openctp_ctp import thostmduserapi as mdapi
from . import BaseController
from .callbacks import MarketDataSpi
from model.market_data import MarketData
from utils.misc import set_req_fields
from db import create_data_collector
from config import DB_TYPE, BUFFER_SIZE, DB_PATH
from utils.logger import main_logger

# 直接导入整个tools模块，以确保我们使用的是全局变量的引用
import controller.tools as tools

# 全局变量，在MarketDataController初始化时根据config_path参数设置
contract_dict = None

# ===================== 行情控制器 =====================


class MarketDataController(BaseController):
    """
    行情控制器
    """

    def __init__(self, conf, api, exchanges="all", app_context=None):
        super().__init__(api, app_context)
        self.conf = conf

        # 初始化应用上下文（如果没有提供）
        if app_context is None:
            from utils.context import AppContext
            self.app_context = AppContext()
        else:
            self.app_context = app_context

        # 直接从instrument.yml加载合约配置，不依赖AppContext
        from controller.tools import generate_contract_dict, generate_contract_exchange_map, init_contract_exchange_map

        # 更新全局变量和tools模块的全局变量
        global contract_dict
        contract_dict = generate_contract_dict()  # 使用默认的instrument.yml路径
        tools.contract_exchange_map = generate_contract_exchange_map(
        )  # 使用默认的instrument.yml路径
        init_contract_exchange_map()  # 使用默认的instrument.yml路径

        # 调试：检查contract_exchange_map是否已经初始化
        main_logger.debug(
            "MDController",
            f"contract_exchange_map type: {type(tools.contract_exchange_map)}")
        if tools.contract_exchange_map is None:
            main_logger.error(
                "MDController",
                "contract_exchange_map is None after initialization!")

        # 解析exchanges参数
        if exchanges == "all":
            # 如果是all，从配置文件中获取所有交易所
            from controller.tools import load_futures_config
            config = load_futures_config()  # 使用默认的instrument.yml路径
            self.exchanges = list(config.keys())
        else:
            self.exchanges = [exch.strip() for exch in exchanges.split(",")]

        # 去重并确保交易所名称有效
        self.exchanges = list(set(self.exchanges))

        # 初始化数据收集器字典，按交易所存储
        self.data_collectors = {}
        for exch in self.exchanges:
            # 为每个交易所创建一个数据收集器
            self.data_collectors[exch] = create_data_collector(
                db_type=DB_TYPE,
                buffer_size=BUFFER_SIZE,
                # 确保数据库文件保存在appfiles/mydb/{db_type}/目录下
                db_path=os.path.join(DB_PATH, DB_TYPE.lower()),
                db_name=f"{exch}.{DB_TYPE.lower()}"
                if DB_TYPE != "CSV" else None)

        # 创建并注册行情数据SPI回调
        self.spi = MarketDataSpi(self)
        self.api.RegisterSpi(self.spi)
        # 订阅相关计数器
        self.subscribed_count = 0
        self.total_to_subscribe = 0

    def login(self):
        """发起行情登录请求"""
        res = self.send_request(
            "ReqUserLogin", {
                "BrokerID": self.conf['broker_id'],
                "UserID": self.conf['investor_id'],
                "Password": self.conf['password']
            }, "ReqUserLogin")

    def subscribe_market_data(self):
        """订阅行情数据"""
        # 根据exchanges参数过滤需要订阅的合约
        filtered_instrument_list = []
        for instrument in contract_dict['all']:
            exchange = tools.contract_exchange_map.get(instrument)
            if exchange in self.exchanges:
                filtered_instrument_list.append(instrument)

        instrument_list = [
            inst.encode("utf-8") for inst in filtered_instrument_list
        ]
        self.total_to_subscribe = len(instrument_list)
        main_logger.info(
            "MDController",
            f"Subscribing to {self.total_to_subscribe} market data contracts from exchanges: {', '.join(self.exchanges)}"
        )
        self.api.SubscribeMarketData(instrument_list, len(instrument_list))

    def process_market_data(self, market_data_dict):
        """处理行情数据"""
        # 获取合约代码
        instrument_id = market_data_dict.get("InstrumentID")
        if not instrument_id:
            main_logger.error("MDController",
                              "Market data without InstrumentID")
            return

        # 找到对应的交易所
        exchange = tools.contract_exchange_map.get(instrument_id)
        if not exchange:
            main_logger.error(
                "MDController",
                f"Exchange not found for instrument {instrument_id}")
            return

        # 将数据添加到对应的交易所数据收集器
        if exchange in self.data_collectors:
            self.data_collectors[exchange].add_data(market_data_dict)
        else:
            main_logger.error(
                "MDController",
                f"No data collector found for exchange {exchange}")
