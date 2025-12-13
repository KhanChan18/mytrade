import os
import sqlite3
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# 获取日志记录器
logger = logging.getLogger(__name__)

class DatabaseInterface(ABC):
    """数据库接口定义"""
    
    @abstractmethod
    def save(self, data: List[Dict[str, Any]]) -> None:
        """保存数据到数据库"""
        pass
    
    @abstractmethod
    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """从数据库加载数据"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """获取数据库中的所有表名"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass

class CSVHandler(DatabaseInterface):
    """CSV文件数据库实现"""
    
    def __init__(self, db_path: str = "db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
    
    def save(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        
        # 使用合约ID作为表名
        table_name = data[0].get("InstrumentID", "default")
        file_path = os.path.join(self.db_path, f"{table_name}.csv")
        
        df = pd.DataFrame(data)
        
        # 如果文件不存在，写入表头
        if not os.path.exists(file_path):
            df.to_csv(file_path, index=False, header=True)
        else:
            df.to_csv(file_path, index=False, header=False, mode='a')
    
    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        file_path = os.path.join(self.db_path, f"{table_name}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Table {table_name} not found")
        
        df = pd.read_csv(file_path)
        if limit:
            df = df.tail(limit)
        
        return df
    
    def get_tables(self) -> List[str]:
        tables = []
        for file in os.listdir(self.db_path):
            if file.endswith(".csv"):
                tables.append(file[:-4])
        return tables
    
    def close(self) -> None:
        # CSV不需要关闭连接
        pass

class SQLiteHandler(DatabaseInterface):
    """SQLite3数据库实现"""
    
    def __init__(self, db_path: str = "db", db_name: str = "market_data.db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.db_file = os.path.join(db_path, db_name)
        self.connection = sqlite3.connect(self.db_file)
    
    def save(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        
        table_name = data[0].get("InstrumentID", "default")
        df = pd.DataFrame(data)
        
        # 写入数据，if_exists='append'表示追加
        df.to_sql(table_name, self.connection, if_exists='append', index=False)
    
    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        
        return pd.read_sql_query(query, self.connection)
    
    def get_tables(self) -> List[str]:
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor = self.connection.cursor()
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def close(self) -> None:
        self.connection.close()

class HDF5Handler(DatabaseInterface):
    """HDF5数据库实现"""
    
    def __init__(self, db_path: str = "db", db_name: str = "market_data.h5"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.db_file = os.path.join(db_path, db_name)
    
    def save(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        
        table_name = data[0].get("InstrumentID", "default")
        df = pd.DataFrame(data)
        
        # 写入HDF5文件
        with pd.HDFStore(self.db_file, mode='a') as store:
            store.append(table_name, df, format='table', append=True)
    
    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        with pd.HDFStore(self.db_file, mode='r') as store:
            if table_name not in store:
                raise KeyError(f"Table {table_name} not found")
            
            df = store[table_name]
            if limit:
                df = df.tail(limit)
            
        return df
    
    def get_tables(self) -> List[str]:
        with pd.HDFStore(self.db_file, mode='r') as store:
            tables = list(store.keys())
        return [table[1:] for table in tables]  # 去掉前面的'/'
    
    def close(self) -> None:
        # HDF5不需要持久连接
        pass

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
        
        logger.info(f"DataCollector initialized with {db_type} database and buffer size {buffer_size}")
    
    def add_data(self, data: Dict[str, Any]) -> None:
        """添加数据到缓冲区"""
        self.buffer.append(data)
        
        # 当缓冲区满时，保存数据
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self) -> None:
        """将缓冲区中的数据写入数据库"""
        if self.buffer:
            logger.debug(f"Flushing {len(self.buffer)} records to database")
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
        logger.info("DataCollector closed")

# 工厂函数，用于创建DataCollector实例
def create_data_collector(db_type: str = "HDF5", buffer_size: int = 128, db_path: str = "db") -> DataCollector:
    """创建数据收集器实例"""
    return DataCollector(db_type, buffer_size, db_path)
