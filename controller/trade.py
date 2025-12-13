# -*- coding: utf-8 -*-
"""交易控制器（TradeController）"""
from openctp_ctp import thosttraderapi as tdapi
from . import BaseController
from .callbacks import TradeSpi
from utils.misc import set_req_fields


class TradeController(BaseController):
    """交易控制器"""
    def __init__(self, conf, api):
        super().__init__(conf, api)
        # 创建并注册交易数据SPI回调
        self.spi = TradeSpi(self)
        self.api.RegisterSpi(self.spi)

    def login(self):
        """发起交易登录请求"""
        res = self.send_request(
            "ReqUserLogin",
            {
                "BrokerID": self.conf['broker_id'],
                "UserID": self.conf['investor_id'],
                "Password": self.conf['password']
            },
            "ReqUserLogin"
        )
