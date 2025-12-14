# -*- coding: utf-8 -*-
"""测试data_collector功能"""
from app_entry import MyTradeApp
import os
import sys
import pathlib
import unittest
import contextlib
from unittest import mock

# 添加项目根目录到Python路径
sys.path.append(str(pathlib.Path(__file__).absolute().parents[3]))


class TestDataCollector(unittest.TestCase):
    """测试data_collector功能"""

    def setUp(self):
        """测试前的准备工作"""
        self.app = MyTradeApp()

    def test_data_collector_single_process(self):
        """测试单进程模式下的data_collector"""
        from utils.logger import main_logger

        with contextlib.ExitStack() as stack:
            # 模拟trading_client.run方法，避免实际运行
            mock_run = stack.enter_context(
                mock.patch.object(self.app._trading_client, 'run'))
            # 模拟logger.set_log_file和set_log_level方法
            stack.enter_context(mock.patch.object(main_logger, 'set_log_file'))
            stack.enter_context(mock.patch.object(
                main_logger, 'set_log_level'))

            # 调用data_collector方法（单进程模式）
            self.app.data_collector(
                platform="TEST", env="test", collector_id="test_id", count=1)

            # 验证trading_client.run是否被正确调用
            mock_run.assert_called_once_with(
                "TEST", "test", api_type="md", exchanges="all")

    def test_data_collector_multi_process(self):
        """测试多进程模式下的data_collector"""
        # 模拟multiprocessing.Process和multiprocessing.Process.start方法
        with contextlib.ExitStack() as stack:
            # 模拟generate_contract_exchange_map函数，返回3个交易所
            stack.enter_context(mock.patch('controller.tools.generate_contract_exchange_map', return_value={
                'contract1': 'EXCH1',
                'contract2': 'EXCH2',
                'contract3': 'EXCH3'
            }))

            # 模拟multiprocessing.Process
            mock_process = stack.enter_context(
                mock.patch('multiprocessing.Process'))

            # 设置模拟对象的返回值
            mock_process_instance = mock.Mock()
            mock_process.return_value = mock_process_instance

            # 调用data_collector方法（多进程模式）
            self.app.data_collector(platform="TEST", env="test", count=3)

            # 验证Process被创建了3次
            self.assertEqual(mock_process.call_count, 3)

            # 验证所有进程都被启动
            mock_process_instance.start.assert_called()

    def test_data_collector_multi_process_logging(self):
        """测试多进程模式下的data_collector日志功能"""
        # 模拟UUID生成，确保每次调用生成不同的UUID
        mock_uuids = ['uuid-1', 'uuid-2', 'uuid-3']

        with contextlib.ExitStack() as stack:
            # 模拟generate_contract_exchange_map函数，返回3个交易所
            stack.enter_context(mock.patch('controller.tools.generate_contract_exchange_map', return_value={
                'contract1': 'EXCH1',
                'contract2': 'EXCH2',
                'contract3': 'EXCH3'
            }))

            # 模拟UUID生成
            stack.enter_context(mock.patch(
                'uuid.uuid4', side_effect=mock_uuids))
            # 模拟multiprocessing.Process
            mock_process = stack.enter_context(
                mock.patch('multiprocessing.Process'))

            # 调用data_collector方法（多进程模式）
            self.app.data_collector(platform="TEST", env="test", count=3)

            # 验证Process被创建了3次，且每次都传递了正确的参数
            self.assertEqual(mock_process.call_count, 3)

            # 获取所有Process调用的参数
            process_calls = mock_process.call_args_list

            # 验证每个进程都传递了正确的target和args（注意：需要包含exchanges参数）
            for i in range(3):
                call_args = process_calls[i][1]
                self.assertEqual(
                    call_args['target'], self.app._process_manager._data_collector_process)
                # 验证进程参数是否正确，args应该包含(exchange, env, uuid, exchange_name)
                self.assertEqual(call_args['args'][0], 'TEST')
                self.assertEqual(call_args['args'][1], 'test')
                self.assertEqual(call_args['args'][2], mock_uuids[i])
                # 第三个参数应该是交易所名称
                self.assertIn(call_args['args'][3], [
                              'EXCH1', 'EXCH2', 'EXCH3'])

    def test_data_collector_process_log_file(self):
        """测试单个data_collector进程的日志文件设置"""
        # 模拟UUID生成
        mock_uuid = 'test-uuid-123'
        from utils.logger import main_logger

        with contextlib.ExitStack() as stack:
            # 模拟UUID生成
            stack.enter_context(mock.patch(
                'uuid.uuid4', return_value=mock_uuid))
            # 模拟config模块中的LOG_PATH
            stack.enter_context(mock.patch(
                'utils.process.LOG_PATH', '/mock/logs'))
            # 模拟os.path.join函数
            mock_path_join = stack.enter_context(mock.patch(
                'os.path.join', side_effect=lambda *args: '/'.join(args)))
            # 模拟trading_client.run方法
            stack.enter_context(mock.patch.object(
                self.app._trading_client, 'run'))
            # 模拟logger.set_log_file和set_log_level方法
            mock_set_log_file = stack.enter_context(
                mock.patch.object(main_logger, 'set_log_file'))
            stack.enter_context(mock.patch.object(
                main_logger, 'set_log_level'))
            stack.enter_context(mock.patch.object(main_logger, 'info'))

            # 直接调用单个进程的方法（单进程模式）
            self.app.data_collector(platform="TEST", env="test", count=1)

            # 验证日志文件路径被正确构造
            mock_path_join.assert_any_call(
                '/mock/logs', f'data_collector_{mock_uuid}.log')

            # 验证设置了正确的日志文件
            mock_set_log_file.assert_any_call(
                '/mock/logs/data_collector_test-uuid-123.log')

    def test_data_collector_parameters(self):
        """测试data_collector的参数处理"""
        from utils.logger import main_logger

        with contextlib.ExitStack() as stack:
            # 模拟trading_client.run方法
            stack.enter_context(mock.patch.object(
                self.app._trading_client, 'run'))
            # 模拟logger相关方法
            stack.enter_context(mock.patch.object(main_logger, 'set_log_file'))
            stack.enter_context(mock.patch.object(
                main_logger, 'set_log_level'))

            # 使用不同的参数调用data_collector
            self.app.data_collector(
                platform="CUSTOM_PLATFORM",
                env="custom_env",
                collector_id="custom_id",
                count=1
            )

            # 验证参数是否被正确传递
            self.app._trading_client.run.assert_called_once_with(
                "CUSTOM_PLATFORM", "custom_env", api_type="md", exchanges="all"
            )

    def test_logger_daily_rotation(self):
        """测试日志按日滚动功能"""
        import datetime
        import os

        # 模拟基础日志文件路径
        base_log_path = "/mock/logs/data_collector_test-uuid.log"

        # 模拟datetime模块，确保在Logger初始化时使用我们的mock
        with mock.patch('utils.logger.datetime') as mock_datetime:
            # 创建日志对象
            from utils.logger import Logger

            # 模拟日期为2025-12-13
            mock_date_1 = mock.Mock()
            mock_date_1.strftime.return_value = "2025-12-13"
            mock_datetime.now.return_value = mock_date_1

            logger = Logger(log_file=base_log_path)

            # 第一次写入日志
            logger._update_log_file()
            first_log_file = logger._current_log_file
            # 验证日志文件路径（使用os.path.normpath处理路径分隔符差异）
            expected_path_1 = os.path.normpath(
                "/mock/logs/data_collector_test-uuid_2025-12-13.log")
            self.assertEqual(os.path.normpath(first_log_file), expected_path_1)

            # 模拟日期变化为2025-12-14
            mock_date_2 = mock.Mock()
            mock_date_2.strftime.return_value = "2025-12-14"
            mock_datetime.now.return_value = mock_date_2

            # 第二次写入日志（日期已变化）
            logger._update_log_file()
            second_log_file = logger._current_log_file
            # 验证日志文件路径（使用os.path.normpath处理路径分隔符差异）
            expected_path_2 = os.path.normpath(
                "/mock/logs/data_collector_test-uuid_2025-12-14.log")
            self.assertEqual(os.path.normpath(
                second_log_file), expected_path_2)

            # 验证两个日志文件路径不同
            self.assertNotEqual(first_log_file, second_log_file)


if __name__ == "__main__":
    unittest.main()
