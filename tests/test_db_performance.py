#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库性能测试脚本"""
from db.collector import create_data_collector
import pytest
from datetime import datetime, timedelta
import shutil
import random
import time
import sys
import os
# 添加项目根目录到Python路径
import pathlib

sys.path.append(str(pathlib.Path(__file__).absolute().parents[2]))


class TestDBPerformance:
    """数据库性能测试类"""

    test_db_path = None

    @classmethod
    def setup_class(cls):
        """在测试类开始前执行"""
        cls.test_db_path = "db_test_performance"

    @classmethod
    def teardown_class(cls):
        """在测试类结束后执行"""
        # 清理临时数据库目录
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)

    def generate_test_data(self, num_records: int) -> list:
        """生成测试数据"""
        test_data = []

        for i in range(num_records):
            # 生成随机的合约代码
            instrument_id = f"RB{random.randint(2501, 2612)}"

            # 生成随机的价格和成交量
            last_price = round(random.uniform(3000, 5000), 2)
            volume = random.randint(0, 100000)

            # 生成随机的盘口数据
            bid_prices = [
                round(last_price - random.uniform(0, 10), 2) for _ in range(5)
            ]
            ask_prices = [
                round(last_price + random.uniform(0, 10), 2) for _ in range(5)
            ]
            bid_volumes = [random.randint(0, 1000) for _ in range(5)]
            ask_volumes = [random.randint(0, 1000) for _ in range(5)]

            # 创建数据记录
            record = {
                "InstrumentID":
                instrument_id,
                "TradingDay":
                (datetime.now() -
                 timedelta(days=random.randint(0, 30))).strftime("%Y%m%d"),
                "ActionDay":
                datetime.now().strftime("%Y%m%d"),
                "UpdateTime":
                datetime.now().strftime("%H:%M:%S"),
                "UpdateMillisec":
                random.randint(0, 999),
                "LastPrice":
                last_price,
                "Volume":
                volume,
                "PreSettlementPrice":
                round(random.uniform(3000, 5000), 2),
                "PreClosePrice":
                round(random.uniform(3000, 5000), 2),
                "PreOpenInterest":
                round(random.uniform(0, 1000000), 2),
                "OpenPrice":
                round(random.uniform(3000, 5000), 2),
                "HighestPrice":
                round(random.uniform(last_price, last_price + 50), 2),
                "LowestPrice":
                round(random.uniform(last_price - 50, last_price), 2),
                "LimitUpPrice":
                round(last_price * 1.05, 2),
                "LimitDownPrice":
                round(last_price * 0.95, 2),
                "OpenInterest":
                round(random.uniform(0, 1000000), 2),
                "Turnover":
                round(last_price * volume, 2),
                "AveragePrice":
                round(last_price * random.uniform(0.99, 1.01), 2),
                # 盘口数据
                "BidPrice1":
                bid_prices[0],
                "BidVolume1":
                bid_volumes[0],
                "AskPrice1":
                ask_prices[0],
                "AskVolume1":
                ask_volumes[0],
                "BidPrice2":
                bid_prices[1],
                "BidVolume2":
                bid_volumes[1],
                "AskPrice2":
                ask_prices[1],
                "AskVolume2":
                ask_volumes[1],
                "BidPrice3":
                bid_prices[2],
                "BidVolume3":
                bid_volumes[2],
                "AskPrice3":
                ask_prices[2],
                "AskVolume3":
                ask_volumes[2],
                "BidPrice4":
                bid_prices[3],
                "BidVolume4":
                bid_volumes[3],
                "AskPrice4":
                ask_prices[3],
                "AskVolume4":
                ask_volumes[3],
                "BidPrice5":
                bid_prices[4],
                "BidVolume5":
                bid_volumes[4],
                "AskPrice5":
                ask_prices[4],
                "AskVolume5":
                ask_volumes[4],
            }

            test_data.append(record)

        return test_data

    @pytest.mark.parametrize("db_type", ["CSV", "SQLite3", "HDF5"])
    def test_write_performance(self, db_type):
        """测试不同数据库的写入性能"""
        # 生成少量测试数据用于单元测试
        num_records = 1000
        test_data = self.generate_test_data(num_records)

        # 创建数据收集器实例
        data_collector = create_data_collector(db_type=db_type,
                                               buffer_size=128,
                                               db_path=self.test_db_path,
                                               db_name="test_db")

        try:
            # 测试写入性能
            start_time = time.time()

            # 模拟实时数据流入
            for record in test_data:
                data_collector.add_data(record)

            # 确保所有数据都被写入
            data_collector.flush()

            end_time = time.time()

            write_time = end_time - start_time
            print(f"{db_type} 写入 {num_records} 条记录耗时: {write_time:.4f} 秒")
            assert write_time > 0  # 确保写入操作完成

        finally:
            # 关闭数据收集器
            data_collector.close()

    @pytest.mark.parametrize("db_type", ["CSV", "SQLite3", "HDF5"])
    def test_read_performance(self, db_type):
        """测试不同数据库的读取性能"""
        # 生成少量测试数据用于单元测试
        num_records = 1000
        read_limit = 500
        test_data = self.generate_test_data(num_records)

        # 创建数据收集器实例
        data_collector = create_data_collector(db_type=db_type,
                                               buffer_size=1,
                                               db_path=self.test_db_path,
                                               db_name="test_db")

        try:
            # 先写入数据
            data_collector.save(test_data)

            # 获取表名
            tables = data_collector.get_tables()
            if not tables:
                pytest.skip("No tables found in database")

            table_name = tables[0]

            # 测试读取性能
            start_time = time.time()
            df = data_collector.load(table_name, read_limit)
            end_time = time.time()

            read_time = end_time - start_time
            print(f"{db_type} 读取 {read_limit} 条记录耗时: {read_time:.4f} 秒")
            assert df.shape[0] <= read_limit  # 确保读取记录数正确

        finally:
            # 关闭数据收集器
            data_collector.close()


def main():
    """主函数，用于独立运行性能测试"""
    import argparse

    parser = argparse.ArgumentParser(description='数据库性能测试脚本')
    parser.add_argument('--records',
                        '-r',
                        type=int,
                        default=10000,
                        help='测试数据记录数，默认10000条')
    parser.add_argument('--buffer',
                        '-b',
                        type=int,
                        default=128,
                        help='缓冲区大小，默认128')
    parser.add_argument('--read_limit',
                        '-l',
                        type=int,
                        default=1000,
                        help='读取测试的记录数，默认1000条')
    args = parser.parse_args()

    print(f"生成 {args.records} 条测试数据...")
    test = TestDBPerformance()
    test_data = test.generate_test_data(args.records)
    print(f"测试数据生成完成")

    # 测试不同的数据库类型
    db_types = ['CSV', 'SQLite3', 'HDF5']

    print("\n开始测试写入性能...")
    print("=" * 50)
    print(f"{'数据库类型':<10} {'写入时间(秒)':<15} {'记录数/秒':<12}")
    print("=" * 50)

    write_results = {}

    for db_type in db_types:
        # 创建数据收集器实例
        data_collector = create_data_collector(db_type=db_type,
                                               buffer_size=args.buffer,
                                               db_path=test.test_db_path)

        # 测试写入性能
        start_time = time.time()

        # 模拟实时数据流入
        for record in test_data:
            data_collector.add_data(record)

        # 确保所有数据都被写入
        data_collector.flush()

        end_time = time.time()

        write_time = end_time - start_time
        data_collector.close()

        records_per_second = args.records / write_time if write_time > 0 else 0
        write_results[db_type] = write_time
        print(f"{db_type:<10} {write_time:<15.4f} {records_per_second:<12.0f}")

    print("\n开始测试读取性能...")
    print("=" * 50)
    print(f"{'数据库类型':<10} {'读取时间(秒)':<15} {'记录数/秒':<12}")
    print("=" * 50)

    read_results = {}

    for db_type in db_types:
        # 创建数据收集器实例
        data_collector = create_data_collector(db_type=db_type,
                                               buffer_size=1,
                                               db_path=test.test_db_path)

        try:
            # 获取表名
            tables = data_collector.get_tables()
            if not tables:
                read_time = -1
            else:
                table_name = tables[0]

                # 测试读取性能
                start_time = time.time()
                df = data_collector.load(table_name, args.read_limit)
                end_time = time.time()

                read_time = end_time - start_time

            records_per_second = args.read_limit / read_time if read_time > 0 else 0
            read_results[db_type] = read_time
            print(
                f"{db_type:<10} {read_time:<15.4f} {records_per_second:<12.0f}"
            )

        finally:
            # 关闭数据收集器
            data_collector.close()

    # 总结
    print("\n性能测试总结：")
    print("=" * 50)

    # 找出写入最快的数据库
    fastest_write = min(write_results, key=write_results.get)
    print(f"写入最快的数据库：{fastest_write} ({write_results[fastest_write]:.4f}秒)")

    # 找出读取最快的数据库
    fastest_read = min(read_results, key=read_results.get)
    print(f"读取最快的数据库：{fastest_read} ({read_results[fastest_read]:.4f}秒)")

    print("\n注意：测试结果可能因硬件配置和系统环境而有所不同。")

    # 清理临时数据库目录
    if os.path.exists(test.test_db_path):
        shutil.rmtree(test.test_db_path)


if __name__ == "__main__":
    # 如果作为脚本运行，执行主函数
    main()
