#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库查询测试脚本"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
import pathlib
sys.path.append(str(pathlib.Path(__file__).absolute().parents[2]))

from db.collector import create_data_collector
from config import DB_TYPE, DB_PATH


class TestQueryDB:
    """数据库查询测试类"""
    
    @pytest.fixture
    def data_collector(self):
        """创建数据收集器实例"""
        return create_data_collector(
            db_type=DB_TYPE,
            buffer_size=1,
            db_path=DB_PATH
        )
    
    def test_get_tables(self, data_collector):
        """测试获取所有表"""
        tables = data_collector.get_tables()
        assert isinstance(tables, list)
    
    def test_load_data_with_limit(self, data_collector):
        """测试加载带限制的数据"""
        tables = data_collector.get_tables()
        if tables:
            table_name = tables[0]
            df = data_collector.load(table_name, limit=5)
            assert df.shape[0] <= 5
    
    @pytest.mark.skipif(not os.path.exists('../db'), reason="No database directory found")
    def test_main_no_table_interactive_quit(self):
        """测试交互式查询退出功能"""
        # 使用subprocess调用脚本，避免相对导入问题
        import subprocess
        # 获取项目根目录路径
        project_root = str(pathlib.Path(__file__).absolute().parents[2])
        query_db_path = os.path.join(project_root, 'query_db.py')
        result = subprocess.run([sys.executable, query_db_path], capture_output=True, text=True)
        assert result.returncode == 0
    
    @pytest.mark.skipif(not os.path.exists('../db'), reason="No database directory found")
    def test_query_with_table_name(self):
        """测试指定表名查询"""
        import subprocess
        # 获取项目根目录路径
        project_root = str(pathlib.Path(__file__).absolute().parents[2])
        db_path = os.path.join(project_root, 'db')
        query_db_path = os.path.join(project_root, 'query_db.py')
        
        # 获取数据库文件列表
        if os.path.exists(db_path):
            tables = os.listdir(db_path)
            if tables:
                # 获取第一个文件的文件名（去掉扩展名）作为表名
                table_name = tables[0].split('.')[0]
                result = subprocess.run([sys.executable, query_db_path, '--table', table_name, '--limit', '3'], 
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert f"表 {table_name} 的前 3 行数据" in result.stdout


if __name__ == "__main__":
    # 可以作为独立脚本运行
    pytest.main([__file__, '-v'])
