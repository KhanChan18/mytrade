# -*- coding: utf-8 -*-
"""交易客户端进程管理逻辑"""
import os
import uuid
import multiprocessing
from config import LOG_CONFIG, LOG_PATH, COLLECTOR_COUNT
from utils.logger import main_logger


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

    def data_collector(self, platform="SIMNOW", env="simulation_7*24",
                       collector_id=None, count=None, exchanges="all"):
        """
        启动行情数据收集器模式
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        :param collector_id: 收集器ID，如果未提供则自动生成UUID（仅单进程模式有效）
        :param count: 收集器进程数量，如果未提供则使用配置文件中的COLLECTOR_COUNT
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
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
                        platform, env, collector_uuid,
                        ','.join(process_exchanges)
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
            self._data_collector_process(
                platform, env, collector_id, exchanges
            )

    def _data_collector_process(
        self, platform, env, collector_id, exchanges="all"
    ):
        """
        单个数据收集器进程的入口函数
        :param platform: 接入平台
        :param env: 运行环境
        :param collector_id: 收集器ID
        :param exchanges: 要订阅的交易所，可选 all 或交易所缩写列表（如 SHFE,DCE），默认 all
        """
        # 设置独立日志配置
        collector_log_file = os.path.join(
            LOG_PATH, f"data_collector_{collector_id}.log"
        )

        try:
            # 动态修改日志文件路径
            main_logger.set_log_file(collector_log_file)
            main_logger.set_log_level(LOG_CONFIG["log_level"])

            main_logger.info(
                "Main",
                f"Starting data_collector | ID: {collector_id} | "
                f"Platform: {platform} | "
                f"Environment: {env} | "
                f"Exchanges: {exchanges}"
            )
            # 运行行情数据收集逻辑
            self.trading_client.run(
                platform, env, api_type="md", exchanges=exchanges
            )
        finally:
            # 恢复原始日志文件路径
            main_logger.set_log_file(LOG_CONFIG["log_file"])

    def _is_trade_controller_running(self):
        """
        检查是否已有trade_controller进程在运行
        通过检查锁文件实现唯一性
        """
        lock_file_path = os.path.join(LOG_PATH, "trade_controller.lock")

        # 尝试创建锁文件
        try:
            # 使用os.O_EXCL标志确保文件不存在时才创建
            fd = os.open(
                lock_file_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644
            )
            os.close(fd)
            return False
        except FileExistsError:
            # 检查锁文件是否是由运行中的进程持有
            # 简单实现：检查文件是否存在即可
            return True

    def trade_controller(self, platform="SIMNOW", env="simulation_7*24"):
        """
        启动交易控制器模式（只允许一个进程）
        :param platform: 接入平台，默认 SIMNOW
        :param env: 运行环境，默认 simulation_7*24
        """
        # 检查是否已有trade_controller进程在运行
        if self._is_trade_controller_running():
            print("Error: trade_controller process is already running. "
                  "Only one instance is allowed.")
            return

        main_logger.info(
            "Main",
            f"Starting trade_controller | Platform: {platform} | "
            f"Environment: {env}"
        )

        # 设置独立日志配置
        trade_logger_file = os.path.join(LOG_PATH, "trade_controller.log")

        try:
            # 动态修改日志文件路径
            main_logger.set_log_file(trade_logger_file)
            main_logger.set_log_level(LOG_CONFIG["log_level"])

            # 运行交易控制逻辑
            self.trading_client.run(platform, env, api_type="trade")
        finally:
            # 恢复原始日志文件路径
            main_logger.set_log_file(LOG_CONFIG["log_file"])
            # 删除锁文件
            lock_file_path = os.path.join(LOG_PATH, "trade_controller.lock")
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
