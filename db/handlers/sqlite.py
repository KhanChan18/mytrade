import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface
from utils.logger import main_logger


class SQLiteHandler(DatabaseInterface):
    """SQLite3数据库实现"""

    def __init__(self, db_path: str, db_name: str):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.db_file = os.path.join(db_path, db_name)

    def save(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        # 按InstrumentID分组数据
        data_by_instrument = {}
        for item in data:
            # 检查InstrumentID是否存在
            instrument_id = item.get("InstrumentID")
            if not instrument_id:
                main_logger.error(
                    "SQLiteHandler", f"缺失InstrumentID的记录: {item}")
                continue
            if instrument_id not in data_by_instrument:
                data_by_instrument[instrument_id] = []
            data_by_instrument[instrument_id].append(item)

        # 每次操作创建新连接
        conn = sqlite3.connect(self.db_file)
        try:
            # 为每个InstrumentID单独保存数据
            for instrument_id, instrument_data in data_by_instrument.items():
                df = pd.DataFrame(instrument_data)
                # 写入数据，if_exists='append'表示追加
                df.to_sql(instrument_id, conn, if_exists='append', index=False)
        finally:
            conn.close()

    def load(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        # 每次操作创建新连接
        conn = sqlite3.connect(self.db_file)
        try:
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            return pd.read_sql_query(query, conn)
        finally:
            conn.close()

    def get_tables(self) -> List[str]:
        # 每次操作创建新连接
        conn = sqlite3.connect(self.db_file)
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            cursor = conn.cursor()
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            conn.close()

    def close(self) -> None:
        # 不需要关闭持久连接
        pass
