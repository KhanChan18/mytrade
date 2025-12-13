# -*- coding: utf-8 -*-
"""交易客户端入口文件"""
import fire
from client import TradingClient, ProcessManager
from utils.logger import main_logger


class MyTradeApp:
    """
    交易客户端应用入口
    提供三种主要功能模式：
    - run: 手动启动CTP客户端，用于程序验证和测试
    - data_collector: 创建行情数据收集守护进程/服务
    - trade_controller: 创建交易控制守护进程/服务
    """
    
    def __init__(self):
        """初始化应用"""
        self._trading_client = TradingClient()
        self._process_manager = ProcessManager(self._trading_client)
    
    # 核心业务方法
    def run(self, platform="SIMNOW", env="simulation_7*24", api_type="trade"):
        """
        手动启动CTP客户端（非守护进程模式）
        用于程序验证、测试和手动操作场景
        
        :param platform: 接入平台，可选 SIMNOW/ZXJT，默认 SIMNOW
        :param env: 运行环境，如 simulation_7*24/verifying/simulation_0，默认 simulation_7*24
        :param api_type: 功能类型，可选 md（行情）/trade（交易），默认 trade
        """
        self._trading_client.run(platform, env, api_type)
    
    # 进程管理方法
    def data_collector(self, platform="SIMNOW", env="simulation_7*24", collector_id=None, count=None):
        """
        创建行情数据收集守护进程/服务
        可启动多个进程同时收集行情数据，每个进程拥有独立的UUID和日志文件
        
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        :param collector_id: 收集器ID，如果未提供则自动生成UUID（仅单进程模式有效）
        :param count: 收集器进程数量，如果未提供则使用配置文件中的COLLECTOR_COUNT
        """
        self._process_manager.data_collector(platform, env, collector_id, count)
    
    def trade_controller(self, platform="SIMNOW", env="simulation_7*24"):
        """
        创建交易控制守护进程/服务
        只允许启动一个进程，用于控制交易执行
        
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        """
        self._process_manager.trade_controller(platform, env)


# ===================== 程序入口（支持命令行 + 直接运行） =====================
if __name__ == "__main__":
    # 通过fire库暴露命令行接口
    fire.Fire(MyTradeApp)