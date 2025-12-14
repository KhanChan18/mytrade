import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.handlers import CSVHandler, SQLiteHandler, HDF5Handler
from utils.logger import main_logger

# 数据库类型映射表：将配置中的小写数据库类型映射到对应的处理器类和默认扩展名
DB_TYPE_MAPPING = {
    "csv": {
        "handler": CSVHandler,
        "default_extension": None  # CSV不需要文件名，使用合约名作为文件名
    },
    "sqlite3": {
        "handler": SQLiteHandler,
        "default_extension": "db"
    },
    "hdf5": {
        "handler": HDF5Handler,
        "default_extension": "h5"
    }
}


class DataCollector:
    """数据收集器，支持多种数据库和缓冲区功能"""

    def __init__(self,
                 db_type: str = "hdf5",
                 buffer_size: int = 128,
                 db_path: str = "db",
                 db_name: str = None):
        self.buffer_size = buffer_size
        self.buffer: List[Dict[str, Any]] = []
        self.db_path = db_path

        # 将数据库类型转换为小写，确保与配置保持一致
        db_type = db_type.lower()

        # 检查数据库类型是否支持
        if db_type not in DB_TYPE_MAPPING:
            supported_types = ', '.join(DB_TYPE_MAPPING.keys())
            raise ValueError(
                f"Unsupported database type: {db_type}. Supported types: {supported_types}"
            )

        # 获取对应的处理器类和默认扩展名
        db_config = DB_TYPE_MAPPING[db_type]
        handler_class = db_config["handler"]
        default_extension = db_config["default_extension"]

        # 创建数据库处理器实例
        if default_extension is None:
            # CSV不需要文件名参数
            self.db_handler = handler_class(db_path)
        else:
            # 其他数据库类型需要文件名参数
            if db_name is None:
                raise ValueError(
                    f"Database type {db_type} requires a db_name parameter.")
            self.db_handler = handler_class(db_path, db_name)

        main_logger.info(
            "DataCollector",
            f"initialized with {db_type} database and buffer size {buffer_size}"
        )

    def add_data(self, data: Dict[str, Any]) -> None:
        """添加数据到缓冲区"""
        self.buffer.append(data)
        # print(f"buffer_length: {self.buffer_size}")
        # 当缓冲区满时，保存数据
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """将缓冲区中的数据写入数据库"""
        if self.buffer:
            main_logger.info(
                "DataCollector",
                f"Flushing {len(self.buffer)} records to database")
            self.db_handler.save(self.buffer)
            self.buffer.clear()

    def save(self, data: List[Dict[str, Any]]) -> None:
        """直接保存数据到数据库"""
        self.db_handler.save(data)

    def load(self,
             table_name: str,
             limit: Optional[int] = None) -> pd.DataFrame:
        """从数据库加载数据"""
        return self.db_handler.load(table_name, limit)

    def get_tables(self) -> List[str]:
        """获取数据库中的所有表名"""
        return self.db_handler.get_tables()

    def close(self) -> None:
        """关闭数据库连接，确保缓冲区中的数据被保存"""
        self.flush()
        self.db_handler.close()
        main_logger.info("DataCollector", "closed")


# 工厂函数，用于创建DataCollector实例


def create_data_collector(db_type: str = "hdf5",
                          buffer_size: int = 128,
                          db_path: str = "db",
                          db_name: str = None) -> DataCollector:
    """创建数据收集器实例"""
    return DataCollector(db_type, buffer_size, db_path, db_name)
