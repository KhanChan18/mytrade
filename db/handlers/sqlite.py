import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface

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