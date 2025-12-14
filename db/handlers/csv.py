import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface
from utils.logger import main_logger


class CSVHandler(DatabaseInterface):
    """CSV文件数据库实现"""

    def __init__(self, db_path: str = "db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)

    def save(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        # 按InstrumentID分组数据
        data_by_instrument = {}
        for item in data:
            # 检查InstrumentID是否存在
            instrument_id = item.get("InstrumentID")
            if not instrument_id:
                main_logger.error("CSVHandler", f"缺失InstrumentID的记录: {item}")
                continue
            if instrument_id not in data_by_instrument:
                data_by_instrument[instrument_id] = []
            data_by_instrument[instrument_id].append(item)
        # 为每个InstrumentID单独保存
        import controller.tools
        # 确保contract_exchange_map已初始化
        if controller.tools.contract_exchange_map is None:
            controller.tools.init_contract_exchange_map()
        for instrument_id, instrument_data in data_by_instrument.items():
            # 获取合约对应的交易所，必须存在于instrument.yml中
            exchange = controller.tools.contract_exchange_map.get(
                instrument_id)
            if not exchange:
                main_logger.error("CSVHandler",
                                  f"合约{instrument_id}不在instrument.yml配置中")
                continue
            # 提取品种前缀（字母部分）作为目录名
            symbol = ''.join([c for c in instrument_id if c.isalpha()])
            if not symbol:
                main_logger.error("CSVHandler", f"合约{instrument_id}无法提取品种前缀")
                continue
            # 创建交易所目录
            exchange_path = os.path.join(self.db_path, exchange)
            os.makedirs(exchange_path, exist_ok=True)
            # 创建品种目录
            symbol_path = os.path.join(exchange_path, symbol)
            os.makedirs(symbol_path, exist_ok=True)
            # 创建合约文件
            file_path = os.path.join(symbol_path, f"{instrument_id}.csv")
            df = pd.DataFrame(instrument_data)
            # 如果文件不存在，写入表头
            if not os.path.exists(file_path):
                df.to_csv(file_path, index=False, header=True)
            else:
                df.to_csv(file_path, index=False, header=False, mode='a')

    def load(self,
             table_name: str,
             limit: Optional[int] = None) -> pd.DataFrame:
        # 获取合约对应的交易所，必须存在于instrument.yml中
        from controller.tools import contract_exchange_map
        exchange = contract_exchange_map.get(table_name)
        if not exchange:
            main_logger.error("CSVHandler",
                              f"合约{table_name}不在instrument.yml配置中")
            raise ValueError(f"合约{table_name}不在instrument.yml配置中")
        # 提取品种前缀（字母部分）作为目录名
        symbol = ''.join([c for c in table_name if c.isalpha()])
        if not symbol:
            main_logger.error("CSVHandler", f"合约{table_name}无法提取品种前缀")
            raise ValueError(f"合约{table_name}无法提取品种前缀")
        file_path = os.path.join(self.db_path, exchange, symbol,
                                 f"{table_name}.csv")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Table {table_name} not found")

        df = pd.read_csv(file_path)
        if limit:
            df = df.tail(limit)

        return df

    def get_tables(self) -> List[str]:
        tables = []
        # 使用os.walk遍历目录结构，替代三重for循环
        for root, _, files in os.walk(self.db_path):
            # 检查当前目录是否是合约文件所在目录（交易所/品种/）
            # 通过检查路径深度来确定：db_path/交易所/品种/合约.csv
            path_parts = root.split(os.sep)
            if len(path_parts) - len(self.db_path.split(os.sep)) == 2:
                # 只处理合约文件所在目录
                for file in files:
                    if file.endswith(".csv"):
                        tables.append(file[:-4])
        return tables

    def close(self) -> None:
        # CSV不需要关闭连接
        pass
