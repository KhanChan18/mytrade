# -*- coding: utf-8 -*-
"""线程工具模块（信号量管理等）"""
import threading
from utils.logger import main_logger


class SemaphoreManager:
    """
    信号量管理器，用于管理线程信号量
    """

    def __init__(self, value=0):
        """
        初始化信号量管理器
        :param value: 信号量初始值，默认为0
        """
        self._semaphore = threading.Semaphore(value)

    def acquire(self, blocking=True, timeout=None):
        """
        获取信号量
        :param blocking: 是否阻塞，默认为True
        :param timeout: 阻塞超时时间，默认为None
        :return: 是否成功获取信号量
        """
        return self._semaphore.acquire(blocking, timeout)

    def release(self, bIsLast=True):
        """
        释放信号量
        :param bIsLast: 是否为最后一个需要释放的信号量，仅用于日志记录
        """
        if not bIsLast:
            return

        try:
            self._semaphore.release()
            main_logger.debug("Semaphore", "信号量已释放")
        except Exception as e:
            main_logger.error("Semaphore", f"信号量释放失败: {e}")

    def get_semaphore(self):
        """
        获取原始信号量对象
        :return: threading.Semaphore对象
        """
        return self._semaphore
