# -*- coding: utf-8 -*-
"""交易客户端核心业务逻辑"""

# 自定义模块
from .market_data_client import MarketDataClient
from .trade_client import TradeClient


class TradingClient:
    """
    交易客户端核心业务逻辑
    代理到MarketDataClient和TradeClient类，实现行情数据和交易功能
    """
    
    def __init__(self):
        """初始化客户端"""
        self.market_data_client = MarketDataClient()
        self.trade_client = TradeClient()

    def run(self, platform="SIMNOW", env="simulation_7*24", api_type="trade"):
        """
        启动CTP客户端（兼容原有逻辑的入口函数）
        :param platform: 接入平台，可选 SIMNOW/ZXJT，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        :param api_type: 功能类型，可选 md（行情）/trade（交易），默认 trade
        """
        if api_type == 'md':
            self.market_data_client.run(platform, env)
        elif api_type == 'trade':
            self.trade_client.run(platform, env)
        else:
            raise ValueError(f"Unsupported API type: {api_type}, only supports md (market data)/trade (trade)")
