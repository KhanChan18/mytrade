# -*- coding: utf-8 -*-
"""上下文管理模块，用于集中存储和管理应用配置信息以及API资源管理"""
import os
import yaml
import threading
from typing import Dict, Any, Callable, Optional, Tuple
from controller.tools import (
    load_futures_config,
    generate_contract_exchange_map,
    generate_contract_dict
)
from config import load_config as load_app_config


class CTPAPIContext:
    """
    CTP API上下文管理器，用于创建和管理CTP API资源
    """

    def __init__(self, api_create_func: Callable, create_args: Tuple = ()):
        """
        初始化CTP API上下文
        :param api_create_func: API创建函数
        :param create_args: API创建参数
        """
        self.api_create_func = api_create_func
        self.create_args = create_args
        self.api_instance = None

    def __enter__(self):
        """进入上下文，创建API实例"""
        self.api_instance = self.api_create_func(*self.create_args)
        return self.api_instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，释放API资源"""
        if self.api_instance:
            self.api_instance.Release()
            self.api_instance = None


class BackgroundThreadContext:
    """
    后台线程上下文管理器，用于创建和管理后台线程
    """

    def __init__(self, target: Callable, args: Tuple = ()):
        """
        初始化后台线程上下文
        :param target: 线程目标函数
        :param args: 线程参数
        """
        self.target = target
        self.args = args
        self.thread = None

    def __enter__(self):
        """进入上下文，启动后台线程"""
        self.thread = threading.Thread(
            target=self.target, args=self.args, daemon=True
        )
        self.thread.start()
        return self.thread

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，等待线程结束"""
        if self.thread and self.thread.is_alive():
            # 不阻塞主线程，使用守护线程模式
            pass


class AppContext:
    """
    应用上下文类，用于集中存储和管理应用配置信息
    只包含应用核心配置(boot.yml)
    """

    def __init__(self, app_config_path: str = "boot.yml"):
        """
        初始化应用上下文
        :param app_config_path: 应用核心配置文件路径，默认boot.yml
        """
        self.app_config_path = app_config_path

        # 应用核心配置
        self.app_config = None
        self.ctp_server = None

        # 加载配置信息
        self.load_config()

    def load_config(self):
        """
        加载应用核心配置信息
        """
        # 加载应用核心配置
        self.app_config, self.ctp_server = \
            load_app_config(self.app_config_path)

    def __getitem__(self, key: str) -> Any:
        """
        支持通过字典方式访问配置信息
        :param key: 配置键名
        :return: 配置值
        """
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        """
        支持通过in操作符检查配置是否存在
        :param key: 配置键名
        :return: 是否存在
        """
        return hasattr(self, key)
