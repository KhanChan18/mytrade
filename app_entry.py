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

        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        main_logger.info("APP_ENTRY", "\t程序启动配置信息")
        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        main_logger.info(
            "APP_ENTRY",
            f"\t配置文件路径: {config_path}"
        )
        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        main_logger.info("APP_ENTRY", "\t应用核心配置")
        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        for key, value in self.app_context.app_config.items():
            main_logger.info("APP_ENTRY", f"\t{key}: {value}")
        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        main_logger.info("APP_ENTRY", "\tCTP服务器配置:")
        main_logger.info(
            "APP_ENTRY",
            "\t===================================="
        )
        for key, value in self.app_context.ctp_server.items():
            if isinstance(value, dict):
                main_logger.info("APP_ENTRY", f"\t{key}:")
                for sub_key, sub_value in value.items():
                    main_logger.info("APP_ENTRY", f"{sub_key}: {sub_value}")
            else:
                main_logger.info("APP_ENTRY", f"\t{key}: {value}")
        main_logger.info("APP_ENTRY", "\t====================================")
        
        # 初始化交易客户端，传递应用上下文
        self._trading_client = ExchangeClient(
            app_context=self.app_context
        )
        # 初始化进程管理器，传递应用上下文
        self._process_manager = ProcessManager(
            self._trading_client,
            app_context=self.app_context
        )

    # 进程管理方法
    def data_collector(
        self, collector_id=None,
        count=None, exchanges="all",
        dev_test=False
    ):
        """
        创建行情数据收集守护进程/服务
        可启动多个进程同时收集行情数据，每个进程拥有独立的UUID和日志文件
        :param dev_test: 开发测试模式，60秒后自动终止，默认False
        """
        self._process_manager.data_collector(
             collector_id=collector_id,
             count=count,
             exchanges=exchanges,
             dev_test=dev_test
        )

    def trade_controller(self):
        """
        创建交易控制守护进程/服务
        只允许启动一个进程，用于控制交易执行
        :param dev_test: 开发测试模式，5秒后自动终止，默认False
        """
        self._process_manager.trade_controller()

if __name__ == "__main__":
    fire.Fire(MyTradeApp)
