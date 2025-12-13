import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.handlers.csv import CSVHandler
from db.handlers.sqlite import SQLiteHandler
from db.handlers.hdf5 import HDF5Handler
from utils.logger import main_logger

class DataCollector:
    """数据收集器，支持多种数据库和缓冲区功能"""
    
    def __init__(self, db_type: str = "HDF5", buffer_size: int = 128, db_path: str = "db"):
        self.buffer_size = buffer_size
        self.buffer: List[Dict[str, Any]] = []
        self.db_path = db_path
        
        # 根据数据库类型创建对应的处理器
        if db_type == "CSV":
            self.db_handler = CSVHandler(db_path)
        elif db_type == "SQLite3":
            self.db_handler = SQLiteHandler(db_path)
        elif db_type == "HDF5":
            self.db_handler = HDF5Handler(db_path)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        main_logger.info("DataCollector", f"initialized with {db_type} database and buffer size {buffer_size}")
    
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
            main_logger.info("DataCollector", f"Flushing {len(self.buffer)} records to database")
            self.db_handler.save(self.buffer)
            self.buffer.clear()
    
    def save(self, data: List[Dict[str, Any]]) -> None:
        """直接保存数据到数据库"""
        self.db_handler.save(data)
    
    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
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
def create_data_collector(db_type: str = "HDF5", buffer_size: int = 128, db_path: str = "db") -> DataCollector:
    """创建数据收集器实例"""
    return DataCollector(db_type, buffer_size, db_path)