import os
import sqlite3
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseInterface(ABC):
    """数据库接口定义"""

    @abstractmethod
    def save(self, data: List[Dict[str, Any]]) -> None:
        """保存数据到数据库"""
        pass

    @abstractmethod
    def load(self,
             table_name: str,
             limit: Optional[int] = None) -> pd.DataFrame:
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
