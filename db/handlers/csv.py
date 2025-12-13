import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface

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