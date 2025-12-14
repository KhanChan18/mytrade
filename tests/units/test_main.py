# -*- coding: utf-8 -*-
"""测试mytrade.py中的功能：data_collector和trade_controller"""
from app_entry import MyTradeApp
import os
import sys
import pathlib

# 添加项目根目录到Python路径
sys.path.append(str(pathlib.Path(__file__).absolute().parents[2]))


def test_data_collector_method():
    """测试data_collector方法存在且可调用"""
    # 创建MyTradeApp实例
    client = MyTradeApp()

    # 验证data_collector方法存在
    assert hasattr(client, 'data_collector'), \
        "MyTradeApp should have data_collector method"

    # 验证data_collector是可调用的
    assert callable(getattr(client, 'data_collector')), \
        "data_collector should be callable"

    print("data_collector method exists and is callable")
    print("data_collector method test passed")


def test_trade_controller_method():
    """测试trade_controller方法存在且可调用"""
    # 创建MyTradeApp实例
    client = MyTradeApp()

    # 验证trade_controller方法存在
    assert hasattr(client, 'trade_controller'), \
        "MyTradeApp should have trade_controller method"

    # 验证trade_controller是可调用的
    assert callable(getattr(client, 'trade_controller')), \
        "trade_controller should be callable"

    print("trade_controller method exists and is callable")
    print("trade_controller method test passed")


if __name__ == "__main__":
    # 运行测试
    test_data_collector_method()
    print("\n" + "="*50 + "\n")
    test_trade_controller_method()
    print("\nAll tests completed!")
