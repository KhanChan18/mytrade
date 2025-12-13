# -*- coding: utf-8 -*-
"""BaseController：公共父类，整合信号量、优雅退出、日志打印（基于Logger）"""
# 导入核心模块
from utils.signal import EXIT_FLAG
from utils.misc import set_req_fields
from config import LOG_CONFIG
from utils.logger import main_logger
from utils.threading import SemaphoreManager


class BaseController:
    """公共父类：整合信号量、优雅退出、日志打印（基于Logger）"""
    def __init__(self, conf=None, api=None):
        self.conf = conf
        self.api = api
        self._request_id = 100
        self.is_logged_in = False
        self.is_running = False
        self.semaphore = SemaphoreManager(0)  # 使用SemaphoreManager替代直接的信号量
        self.OrderRef = 0  # td_demo的报单引用

    @property
    def request_id(self):
        """自增请求ID"""
        self._request_id += 1
        return self._request_id
    
    def send_request(self, req_type, req_fields, api_method_name, *args, **kwargs):
        """标准化的请求发送方法
        
        Args:
            req_type: 请求类型（用于日志记录）
            req_fields: 请求字段字典
            api_method_name: API方法名称
            *args: 额外的位置参数
            **kwargs: 额外的关键字参数
        
        Returns:
            API方法的返回值
        """
        try:
            # 获取API方法
            api_method = getattr(self.api, api_method_name)
            
            # 创建请求对象
            # 直接从API实例中获取模块，解决__module__返回字符串的问题
            api_module = type(self.api).__module__
            if "thostmduserapi" in api_module:
                from openctp_ctp import thostmduserapi as mdapi
                req_class = getattr(mdapi, f"CThostFtdc{req_type}Field")
            elif "thosttraderapi" in api_module:
                from openctp_ctp import thosttraderapi as tdapi
                req_class = getattr(tdapi, f"CThostFtdc{req_type}Field")
            else:
                raise ValueError(f"Unknown API module: {api_module}")
            
            req = req_class()
            
            # 设置请求字段
            set_req_fields(req, req_fields)
            
            # 获取请求ID
            req_id = self.request_id
            
            # 发起请求
            result = api_method(req, req_id, *args, **kwargs)
            
            main_logger.debug("BaseController", f"Sent {req_type} request, RequestID: {req_id}")
            return result
        except Exception as e:
            main_logger.error("BaseController", f"Failed to send {req_type} request: {e}")
            return -1

    def start(self):
        """启动API（替代td_demo的Run）"""
        self.is_running = True
        main_logger.info("BaseController", "Starting CTP API")
        self.api.Init()

    def stop(self):
        """优雅停止（来自td_demo）"""
        if not self.is_running:
            return
        main_logger.info("BaseController", "Starting to stop CTP API...")
        self.is_running = False
        EXIT_FLAG.set()
        try:
            self.api.RegisterFront("")
            self.api.Release()
            main_logger.info("BaseController", "CTP API has been safely released")
        except Exception as e:
            main_logger.error("BaseController", f"Failed to release API: {e}")

    # 公共回调（抽离重复逻辑，处理pRspInfo为None的情况 + 日志）
    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """公共错误回调"""
        if pRspInfo is None:
            main_logger.error("OnRspError", f"RequestID={nRequestID}, pRspInfo is None")
        else:
            err_msg = pRspInfo.ErrorMsg.encode('gbk', 'ignore') if pRspInfo.ErrorMsg else 'None'
            main_logger.error("OnRspError", f"RequestID={nRequestID}, ErrorID={pRspInfo.ErrorID}, Msg={err_msg}")
        self.semaphore.release(bIsLast)
    
    def check_response_error(self, component_name, pRspInfo, error_type=""):
        """检查响应是否有错误
        
        Args:
            component_name: 组件名称（用于日志记录）
            pRspInfo: 响应信息对象
            error_type: 错误类型（用于日志记录）
            
        Returns:
            bool: 如果有错误返回True，否则返回False
        """
        # 处理pRspInfo为None的情况
        if pRspInfo is None:
            main_logger.error(component_name, f"{error_type} failed: pRspInfo is None")
            EXIT_FLAG.set()
            return True
        
        # 利用日志类的print_error方法
        if main_logger.print_error(f"{component_name}_{error_type}", pRspInfo):
            EXIT_FLAG.set()
            return True
        
        return False

    def OnHeartBeatWarning(self, nTimeLapse):
        """公共心跳警告"""
        main_logger.debug("OnHeartBeatWarning", f"Heartbeat timeout warning: {nTimeLapse} seconds")

    def OnFrontDisconnected(self, nReason):
        """公共断开回调"""
        main_logger.error("OnFrontDisconnected", f"Front server disconnected, reason: {nReason}")
        EXIT_FLAG.set()
