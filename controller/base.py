# -*- coding: utf-8 -*-
"""BaseController：公共父类，整合信号量、优雅退出、日志打印（基于CTPLogger）"""
# 导入核心模块
import threading
from signal_handler import EXIT_FLAG
from utils import set_req_fields
from config import LOG_CONFIG
from logger import CTPLogger


class BaseController:
    """公共父类：整合信号量、优雅退出、日志打印（基于CTPLogger）"""
    def __init__(self, conf=None, api=None):
        self.conf = conf
        self.api = api
        self._request_id = 100
        self.login = False
        self.is_running = False
        self.semaphore = threading.Semaphore(0)  # td_demo的信号量
        self.OrderRef = 0  # td_demo的报单引用
        
        # 初始化日志类（接入配置中的日志参数）
        self.logger = CTPLogger(
            log_file=LOG_CONFIG["log_file"],
            log_level=LOG_CONFIG["log_level"]
        )
        self.logger.set_semaphore(self.semaphore)  # 设置信号量

    @property
    def request_id(self):
        """自增请求ID"""
        self._request_id += 1
        return self._request_id

    def start(self):
        """启动API（替代td_demo的Run）"""
        self.is_running = True
        self.logger.info("BaseController", "启动CTP API")
        self.api.Init()

    def stop(self):
        """优雅停止（来自td_demo）"""
        if not self.is_running:
            return
        self.logger.info("BaseController", "开始停止CTP API...")
        self.is_running = False
        EXIT_FLAG.set()
        try:
            self.api.RegisterFront("")
            self.api.Release()
            self.logger.info("BaseController", "CTP API已安全释放")
        except Exception as e:
            self.logger.error("BaseController", f"释放API失败: {e}")

    # 公共回调（抽离重复逻辑，处理pRspInfo为None的情况 + 日志）
    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """公共错误回调"""
        if pRspInfo is None:
            self.logger.error("OnRspError", f"RequestID={nRequestID}, pRspInfo为None")
        else:
            err_msg = pRspInfo.ErrorMsg.encode('gbk', 'ignore') if pRspInfo.ErrorMsg else 'None'
            self.logger.error("OnRspError", f"RequestID={nRequestID}, ErrorID={pRspInfo.ErrorID}, Msg={err_msg}")
        self.logger.release_semaphore(bIsLast)

    def OnHeartBeatWarning(self, nTimeLapse):
        """公共心跳警告"""
        self.logger.debug("OnHeartBeatWarning", f"心跳超时警告: {nTimeLapse}秒")

    def OnFrontDisconnected(self, nReason):
        """公共断开回调"""
        self.logger.error("OnFrontDisconnected", f"前置机断开，原因: {nReason}")
        EXIT_FLAG.set()
