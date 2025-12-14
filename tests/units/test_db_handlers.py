# -*- coding: utf-8 -*-
"""
测试数据库处理器的存储逻辑
验证是否按InstrumentID正确分表存储
"""
from controller.tools import init_contract_exchange_map
from db.handlers.hdf5 import HDF5Handler
from db.handlers.sqlite import SQLiteHandler
from db.handlers.csv import CSVHandler
import sys
import os
import unittest
import tempfile
import shutil
import pandas as pd
import sqlite3
# 添加项目根目录到Python路径
import pathlib
sys.path.append(str(pathlib.Path(__file__).absolute().parents[3]))


class TestDBHandlers(unittest.TestCase):
    """测试数据库处理器"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()

        # 创建测试用的instrument.yml配置文件
        self.instrument_yml = os.path.join(self.temp_dir, 'instrument.yml')
        import yaml
        config_content = {
            'DCE': {
                'products': ['ad#豆粕期权']
            },
            'SHFE': {
                'products': ['ag#白银期货']
            },
            'CFFEX': {
                'products': ['IM#中证1000指数期货']
            }
        }
        with open(self.instrument_yml, 'w') as f:
            yaml.dump(config_content, f)

        # 初始化全局合约-交易所映射
        init_contract_exchange_map(self.instrument_yml)

        # 获取当前月份和下一个月份，用于生成测试合约代码
        import datetime
        today = datetime.date.today()
        curr_year, curr_month = today.year, today.month

        # 生成当前月份和下一个月份的合约代码
        if curr_month == 12:
            next_year, next_month = curr_year + 1, 1
        else:
            next_year, next_month = curr_year, curr_month + 1

        # 生成月份后缀
        curr_ym = f"{str(curr_year)[-2:]}{curr_month:02d}"
        next_ym = f"{str(next_year)[-2:]}{next_month:02d}"

        # 测试数据
        self.test_data = [
            {"InstrumentID": f"ad{next_ym}", "Price": 100.0, "Volume": 10},
            {"InstrumentID": f"ad{next_ym}", "Price": 101.0, "Volume": 20},
            {"InstrumentID": f"ad{curr_ym}", "Price": 99.0, "Volume": 5},
            {"InstrumentID": f"ag{next_ym}", "Price": 5000.0, "Volume": 15},
            {"InstrumentID": f"ag{next_ym}", "Price": 5010.0, "Volume": 25},
            {"InstrumentID": f"IM{next_ym}", "Price": 3000.0, "Volume": 8},
        ]
        # 保存月份后缀供测试用例使用
        self.curr_ym = curr_ym
        self.next_ym = next_ym

    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)

    def test_csv_handler_save(self):
        """测试CSVHandler的save方法"""
        # 创建CSVHandler实例
        csv_handler = CSVHandler(db_path=self.temp_dir)

        # 保存测试数据
        csv_handler.save(self.test_data)

        # 验证文件结构
        from controller.tools import contract_exchange_map

        # 验证合约文件
        expected_instruments = [
            f"ad{self.next_ym}", f"ad{self.curr_ym}", f"ag{self.next_ym}", f"IM{self.next_ym}"]
        for instrument_id in expected_instruments:
            exchange = contract_exchange_map.get(instrument_id, "default")
            symbol = ''.join([c for c in instrument_id if c.isalpha()])
            file_path = os.path.join(
                self.temp_dir, exchange, symbol, f"{instrument_id}.csv")
            self.assertTrue(os.path.exists(file_path), f"合约文件 {file_path} 不存在")

            # 验证文件内容
            df = pd.read_csv(file_path)
            self.assertIn("InstrumentID", df.columns)
            # 确保文件中只有该合约的数据
            self.assertEqual(df["InstrumentID"].unique()[0], instrument_id)

    def test_sqlite_handler_save(self):
        """测试SQLiteHandler的save方法"""
        # 创建SQLiteHandler实例
        sqlite_handler = SQLiteHandler(
            db_path=self.temp_dir, db_name="test_market_data.db")

        # 保存测试数据
        sqlite_handler.save(self.test_data)

        # 验证数据库文件
        db_file = os.path.join(self.temp_dir, "test_market_data.db")
        self.assertTrue(os.path.exists(db_file), f"SQLite数据库文件 {db_file} 不存在")

        # 验证表结构
        conn = sqlite3.connect(db_file)
        try:
            # 获取所有表名
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            # 验证是否创建了正确的表
            expected_tables = ["ad2601", "ad2512", "ag2601", "IM2601"]
            for table in expected_tables:
                self.assertIn(table, tables, f"表 {table} 不存在")

                # 验证表内容
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                self.assertIn("InstrumentID", df.columns)
                # 确保表中只有该合约的数据
                self.assertEqual(df["InstrumentID"].unique()[0], table)
        finally:
            conn.close()

        # 显式关闭SQLiteHandler的连接
        sqlite_handler.close()

    def test_hdf5_handler_save(self):
        """测试HDF5Handler的save方法"""
        # 创建HDF5Handler实例
        hdf5_handler = HDF5Handler(
            db_path=self.temp_dir, db_name="test_market_data.h5")

        # 保存测试数据
        hdf5_handler.save(self.test_data)

        # 验证HDF5文件
        hdf5_file = os.path.join(self.temp_dir, "test_market_data.h5")
        self.assertTrue(os.path.exists(hdf5_file), f"HDF5文件 {hdf5_file} 不存在")

        # 验证表结构
        with pd.HDFStore(hdf5_file, mode='r') as store:
            tables = list(store.keys())
            # 去掉表名前面的'/'
            tables = [table[1:] for table in tables]

            # 验证是否创建了正确的表
            expected_tables = ["ad2601", "ad2512", "ag2601", "IM2601"]
            for table in expected_tables:
                self.assertIn(table, tables, f"表 {table} 不存在")

                # 验证表内容
                df = store[table]
                self.assertIn("InstrumentID", df.columns)
                # 确保表中只有该合约的数据
                self.assertEqual(df["InstrumentID"].unique()[0], table)


if __name__ == "__main__":
    unittest.main()
