import os
import pandas as pd
from typing import List, Dict, Any, Optional
from db.interface import DatabaseInterface
from utils.logger import main_logger


class HDF5Handler(DatabaseInterface):
    """HDF5数据库实现"""

    def __init__(self, db_path: str, db_name: str):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        # 为HDF5文件添加.h5扩展名
        if not db_name.endswith('.h5'):
            db_name += '.h5'
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
                main_logger.error("HDF5Handler", f"缺失InstrumentID的记录: {item}")
                continue
            if instrument_id not in data_by_instrument:
                data_by_instrument[instrument_id] = []
            data_by_instrument[instrument_id].append(item)

        # 为每个InstrumentID单独保存数据
        with pd.HDFStore(self.db_file, mode='a') as store:
            for instrument_id, instrument_data in data_by_instrument.items():
                df = pd.DataFrame(instrument_data)
                # 写入HDF5文件
                store.append(instrument_id, df, format='table', append=True)

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
