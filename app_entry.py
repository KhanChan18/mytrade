# -*- coding: utf-8 -*-"""交易客户端入口文件"""
import fire
from client import ExchangeClient, ProcessManager
from utils.logger import main_logger
from config import COLLECTOR_COUNT, DATA_COLLECTION_CONFIG
from utils.context import AppContext


class MyTradeApp:
    """
    交易客户端应用入口
    提供三种主要功能模式：
    - run: 手动启动CTP客户端，用于程序验证和测试
    - data_collector: 创建行情数据收集守护进程/服务
    - trade_controller: 创建交易控制守护进程/服务
    """

    def __init__(self, config_path="boot.yml"):
        """
        初始化应用

        :param config_path: 应用核心配置文件路径，默认boot.yml
        """
        # 创建应用上下文，使用指定的配置文件路径
        self.app_context = AppContext(app_config_path=config_path)
        # 初始化交易客户端，传递应用上下文
        self._trading_client = ExchangeClient(app_context=self.app_context)
        # 初始化进程管理器，传递应用上下文
        self._process_manager = ProcessManager(self._trading_client,
                                               app_context=self.app_context)

    # 核心业务方法
    def run(self):
        """
        手动启动CTP客户端（非守护进程模式）
        用于程序验证、测试和手动操作场景
        """
        self._trading_client.run()

    # 进程管理方法
    def data_collector(self,
                       platform="SIMNOW",
                       env="simulation_7*24",
                       collector_id=None,
                       count=None,
                       exchanges="all"):
        """
        创建行情数据收集守护进程/服务
        可启动多个进程同时收集行情数据，每个进程拥有独立的UUID和日志文件
        """
        self._process_manager.data_collector(platform=platform,
                                             env=env,
                                             collector_id=collector_id,
                                             count=count,
                                             exchanges=exchanges)

    def trade_controller(self, platform="SIMNOW", env="simulation_7*24"):
        """
        创建交易控制守护进程/服务
        只允许启动一个进程，用于控制交易执行
        """
        self._process_manager.trade_controller(platform=platform, env=env)


# ===================== 程序入口（支持命令行 + 直接运行） =====================
if __name__ == "__main__":
    # 通过fire库暴露命令行接口
    fire.Fire(MyTradeApp)
