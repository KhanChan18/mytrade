# -*- coding: utf-8 -*-
"""交易客户端进程管理逻辑"""
import multiprocessing
import os
import time
import threading
import uuid

from config import LOG_CONFIG, LOG_PATH, COLLECTOR_COUNT
from utils.logger import main_logger
from utils.signal import EXIT_FLAG


class ProcessManager:
    """
    交易客户端进程管理器
    负责管理data_collector和trade_controller进程
    """

    def __init__(self, trading_client, app_context):
        """
        初始化进程管理器
        :param trading_client: ExchangeClient实例
        :param app_context: 应用上下文实例
        """
        self.trading_client = trading_client
        self.app_context = app_context

    def data_collector(self, collector_id=None, count=None, exchanges="all", dev_test=False):
        """
        启动行情数据收集器模式
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        :param collector_id: 收集器ID，如果未提供则自动生成UUID（仅单进程模式有效）
        :param count: 收集器进程数量，如果未提供则使用配置文件中的COLLECTOR_COUNT
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
        :param dev_test: 开发测试模式，60秒后自动终止，默认False
        """
        # 确定收集器进程数量
        num_collectors = count if count is not None else COLLECTOR_COUNT

        # 进程数检验
        if num_collectors < 1:
            raise ValueError(f"进程数必须大于0，当前值为: {num_collectors}")

        if num_collectors > 1:
            # 多进程模式 - 按交易所分配进程
            # 获取所有可用交易所
            from controller.tools import (
                generate_contract_exchange_map,
                load_futures_config
            )
            # 动态加载instrument.yml配置
            contract_exchange_map = generate_contract_exchange_map()
            all_exchanges = list(set(contract_exchange_map.values()))

            # 检查交易所数量和进程数的关系
            num_exchanges = len(all_exchanges)
            if num_collectors != num_exchanges:
                raise ValueError(
                    f"进程数({num_collectors})必须等于1或交易所数量({num_exchanges})。"
                    "请在配置文件的data_collection中配置正确的订阅关系。"
                )

            # 将交易所分配给不同的进程
            processes = []
            for i in range(num_collectors):
                # 分配部分交易所给每个进程
                process_exchanges = [
                    all_exchanges[j]
                    for j in range(len(all_exchanges))
                    if j % num_collectors == i
                ]
                if not process_exchanges:
                    continue  # 如果没有分配到交易所，跳过

                collector_uuid = str(uuid.uuid4())
                proc = multiprocessing.Process(
                    target=self._data_collector_process,
                    args=(
                        collector_uuid,
                        ','.join(process_exchanges),
                        dev_test
                    )
                )
                processes.append(proc)
                proc.start()
                main_logger.info(
                    "Main",
                    f"Started data_collector process {i+1}/{num_collectors} | "
                    f"ID: {collector_uuid} | "
                    f"Exchanges: {','.join(process_exchanges)}"
                )

            # 等待所有进程结束
            for proc in processes:
                proc.join()
        else:
            # 单进程模式 - 处理所有交易所
            if collector_id is None:
                collector_id = str(uuid.uuid4())
            self._data_collector_process(collector_id, exchanges, dev_test)

    def _data_collector_process(self, collector_id, exchanges="all", dev_test=False):
        """
        单个数据收集器进程的入口函数
        :param platform: 接入平台
        :param env: 运行环境
        :param collector_id: 收集器ID
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
        :param dev_test: 开发测试模式，60秒后自动终止，默认False
        """
        # 设置独立日志配置
        collector_log_file = os.path.join(
            LOG_PATH, f"data_collector_{collector_id}.log"
        )

        try:
            # 动态修改日志文件路径
            main_logger.set_log_file(collector_log_file)
            main_logger.set_log_level(LOG_CONFIG["log_level"])
            # 开发测试模式：60秒后自动终止
            if dev_test:
                # 启动自动退出线程
                exit_thread = threading.Thread(target=_auto_exit, daemon=True)
                exit_thread.start()
            main_logger.info(
                "Main",
                f"Starting data_collector | ID: {collector_id} | "
                f"TCP Address: {self.app_context.ctp_server['md_server']} | "
                f"Exchanges: {exchanges}"
                f"{' | Dev test mode' if dev_test else ''}"
            )
            # 运行行情数据收集逻辑
            self.trading_client.run(api_type="md", exchanges=exchanges)
        finally:
            # 恢复原始日志文件路径
            main_logger.set_log_file(LOG_CONFIG["log_file"])

    def trade_controller(self):
        """
        启动交易控制器模式（允许启动多个进程）
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        """
        main_logger.info(
            "Main",
            "Starting trade_controller to "
            f"{self.app_context.ctp_server['trade_server']}"
        )
        # 设置独立日志文件
        trade_logger_file = os.path.join(LOG_PATH, "trade_controller.log")
        try:
            # 动态修改日志文件路径
            main_logger.set_log_file(trade_logger_file)
            main_logger.set_log_level(LOG_CONFIG["log_level"])

            # 运行交易控制逻辑
            self.trading_client.run(api_type="trade")
        finally:
            # 恢复原始日志文件路径
            main_logger.set_log_file(LOG_CONFIG["log_file"])


def _auto_exit(sec=5):
    main_logger.info("Main", f"Dev test mode: Auto exit in {sec} seconds...")
    time.sleep(sec)
    main_logger.info("Main", f"Dev test mode: Exiting now...")
    EXIT_FLAG.set()