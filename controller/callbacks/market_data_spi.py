# -*- coding: utf-8 -*-
"""行情数据SPI回调处理类"""
from openctp_ctp import thostmduserapi as mdapi
from model.market_data import MarketData
from utils.signal import EXIT_FLAG
from utils.logger import main_logger


class MarketDataSpi(mdapi.CThostFtdcMdSpi):
    """行情数据SPI回调处理类"""

    def __init__(self, controller):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.controller = controller

    def OnFrontConnected(self):
        """行情连接成功"""
        main_logger.info(
            "MDController", "Front server connected, starting login")
        self.controller.login()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """行情登录响应"""
        # 使用统一的错误检查方法
        if self.controller.check_response_error("MDController", pRspInfo, "Login"):
            self.controller.semaphore.release(bIsLast)
            return

        self.controller.is_logged_in = True
        trading_day = pRspUserLogin.TradingDay if pRspUserLogin else 'unknown'
        main_logger.info(
            "MDController", f"Login successful, trading day: {trading_day}")
        self.controller.subscribe_market_data()
        self.controller.semaphore.release(bIsLast)

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """行情推送"""
        if pDepthMarketData is None:
            main_logger.error(
                "MDController", "Market data push: pDepthMarketData is None")
            return
        # 将行情对象转换为MarketData实例
        market_data = MarketData(pDepthMarketData)

        # 将行情数据添加到数据收集器
        self.controller.process_market_data(market_data.to_dict())

    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """行情订阅响应"""
        # 使用统一的错误检查方法
        if self.controller.check_response_error("MDController", pRspInfo, "Subscribe"):
            self.controller.semaphore.release(bIsLast)
            return

        self.controller.subscribed_count += 1

        # 只在最后一个响应时记录订阅总数
        if bIsLast:
            main_logger.info(
                "MDController", f"Successfully subscribed to {self.controller.subscribed_count} out of {self.controller.total_to_subscribe} market data contracts")

        self.controller.semaphore.release(bIsLast)
