# -*- coding: utf-8 -*-
"""交易数据SPI回调处理类"""
from openctp_ctp import thosttraderapi as tdapi
from utils.signal import EXIT_FLAG
from utils.logger import main_logger


class TradeSpi(tdapi.CThostFtdcTraderSpi):
    """交易数据SPI回调处理类"""
    def __init__(self, controller):
        tdapi.CThostFtdcTraderSpi.__init__(self)
        self.controller = controller
    
    def OnFrontConnected(self):
        """交易前置机连接成功"""
        main_logger.info("TradeController", "Trading front server connected, starting login")
        self.controller.login()
    
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """交易登录响应"""
        # 使用统一的错误检查方法
        if self.controller.check_response_error("TradeController", pRspInfo, "Login"):
            self.controller.semaphore.release(bIsLast)
            return
        
        self.controller.is_logged_in = True
        trading_day = pRspUserLogin.TradingDay if pRspUserLogin else 'unknown'
        main_logger.info("TradeController", f"Login successful, trading day: {trading_day}")
        
        # 登录成功后可以执行其他操作，如查询投资者持仓、资金等
        self.controller.semaphore.release(bIsLast)