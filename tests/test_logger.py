# -*- coding: utf-8 -*-
"""测试日志系统功能：验证不同级别日志的格式和控制"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import CTPLogger

def test_logger_info_format():
    """测试INFO级别日志格式"""
    # 捕获标准输出
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    # 创建日志实例
    logger = CTPLogger(log_file=None, log_level="INFO")
    logger.info("Test", "这是一条INFO级别日志")
    
    # 获取输出内容
    output = sys.stdout.getvalue().strip()
    sys.stdout = old_stdout
    
    # 验证输出格式（不含调用位置信息）
    assert re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] \[INFO\] Test: 这是一条INFO级别日志$', output)
    assert "(" not in output  # 确保没有函数名
    assert ":" not in output.split(" ")[-3]  # 确保没有行号

def test_logger_error_format():
    """测试ERROR级别日志格式"""
    # 捕获标准输出
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    # 创建日志实例
    logger = CTPLogger(log_file=None, log_level="INFO")
    logger.error("Test", "这是一条ERROR级别日志")
    
    # 获取输出内容
    output = sys.stdout.getvalue().strip()
    sys.stdout = old_stdout
    
    # 验证输出格式（不含调用位置信息）
    assert re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] \[ERROR\] Test: 这是一条ERROR级别日志$', output)
    assert "(" not in output  # 确保没有函数名
    assert ":" not in output.split(" ")[-3]  # 确保没有行号

def test_logger_debug_format():
    """测试DEBUG级别日志格式"""
    # 捕获标准输出
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    # 创建日志实例
    logger = CTPLogger(log_file=None, log_level="DEBUG")
    logger.debug("Test", "这是一条DEBUG级别日志")
    
    # 获取输出内容
    output = sys.stdout.getvalue().strip()
    sys.stdout = old_stdout
    
    # 验证输出格式（包含调用位置信息）
    assert re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] \[DEBUG\] \[.*?:\d+\(.*?\)\] Test: 这是一条DEBUG级别日志$', output)
    assert "(" in output  # 确保有函数名
    assert ":" in output.split(" ")[3]  # 确保调用位置信息中包含冒号

def test_logger_level_control():
    """测试日志级别控制"""
    # 捕获标准输出
    import io
    
    # 测试INFO级别下DEBUG日志是否被过滤
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    logger = CTPLogger(log_file=None, log_level="INFO")
    logger.debug("Test", "这是一条DEBUG级别日志（应该不显示）")
    
    output = sys.stdout.getvalue().strip()
    sys.stdout = old_stdout
    
    assert output == ""  # DEBUG日志应该被过滤
    
    # 测试DEBUG级别下DEBUG日志是否显示
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    logger._log_level = "DEBUG"
    logger.debug("Test", "这是一条DEBUG级别日志（应该显示）")
    
    output = sys.stdout.getvalue().strip()
    sys.stdout = old_stdout
    
    assert output != ""  # DEBUG日志应该显示
    assert "DEBUG" in output
