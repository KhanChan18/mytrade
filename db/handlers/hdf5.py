import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface

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
        if not os.path.exists(self.db_file):
            return []
        with pd.HDFStore(self.db_file, mode='r') as store:
            tables = list(store.keys())
        return [table[1:] for table in tables]  # 去掉前面的'/'
    
    def close(self) -> None:
        # HDF5不需要持久连接
        pass