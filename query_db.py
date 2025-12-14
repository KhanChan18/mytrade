#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库查询脚本"""
import argparse
from config import DB_TYPE, DB_PATH
from db import create_data_collector
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库查询脚本')
    parser.add_argument('--table', '-t', type=str, help='表名，如果不指定则显示所有表')
    parser.add_argument('--limit',
                        '-l',
                        type=int,
                        default=10,
                        help='显示前N行数据，默认10行')
    parser.add_argument('--db_type',
                        '-d',
                        type=str,
                        default=DB_TYPE,
                        help='数据库类型（CSV/SQLite3/HDF5）')
    args = parser.parse_args()

    try:
        # 创建数据收集器实例
        data_collector = create_data_collector(
            db_type=args.db_type,
            buffer_size=1,  # 查询时不需要缓冲区
            db_path=DB_PATH,
            db_name="query_db" if args.db_type.lower() != "csv" else None)

        if not args.table:
            # 显示所有表
            tables = data_collector.get_tables()
            if not tables:
                print("数据库中没有表")
                return

            print(f"数据库中的表（{args.db_type}）：")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")

            # 询问用户是否要查看某个表的数据
            while True:
                table_choice = input("\n请输入要查看的表编号（按Enter退出）：")
                if not table_choice:
                    break

                try:
                    table_index = int(table_choice) - 1
                    if 0 <= table_index < len(tables):
                        table_name = tables[table_index]
                        df = data_collector.load(table_name, args.limit)
                        print(f"\n表 {table_name} 的前 {args.limit} 行数据：")
                        print(df)
                    else:
                        print("无效的表编号")
                except ValueError:
                    print("请输入有效的数字")
        else:
            # 查看指定表的数据
            df = data_collector.load(args.table, args.limit)
            print(f"表 {args.table} 的前 {args.limit} 行数据：")
            print(df)

    except Exception as e:
        print(f"查询出错：{e}")
    finally:
        if 'data_collector' in locals():
            data_collector.close()


if __name__ == "__main__":
    main()
