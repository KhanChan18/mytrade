# -*- coding: utf-8 -*-
"""交易客户端包"""
from utils.process import ProcessManager
from .market_data_client import MarketDataClient
from .trade_client import TradeClient


class ExchangeClient:
    """
    交易客户端核心业务逻辑
    代理到MarketDataClient和TradeClient类，实现行情数据和交易功能
    """

    def __init__(self, app_context):
        """初始化客户端"""
        self.app_context = app_context
        self.market_data_client = MarketDataClient()
        self.trade_client = TradeClient()

    def run(self, api_type=None, exchanges=None):
        """
        启动CTP客户端（兼容原有逻辑的入口函数）
        :param platform: 接入平台，可选 SIMNOW/ZXJT，默认从app_context获取
        :param env: 运行环境
            如 simulation_7*24/verifying/simulation_0，默认从app_context获取
        :param api_type: 功能类型，可选 md（行情）/trade（交易），默认从app_context获取
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），
        默认从app_context获取
        """

        if api_type == 'md':
            self.market_data_client.run(
                exchanges=exchanges,
                app_context=self.app_context
            )
        elif api_type == 'trade':
            self.trade_client.run(app_context=self.app_context)
        else:
            raise ValueError(
                f"Unsupported API type: {api_type}, "
                "only supports md (market data)/trade (trade)"
            )
