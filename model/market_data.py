# -*- coding: utf-8 -*-
"""行情数据模型"""


class MarketData:
    """
    行情数据模型类
    用于封装CTP API返回的行情数据
    """

    def __init__(self, pDepthMarketData):
        """
        初始化行情数据模型
        :param pDepthMarketData: CTP API返回的行情数据对象
        """
        self.InstrumentID = pDepthMarketData.InstrumentID
        self.TradingDay = getattr(pDepthMarketData, "TradingDay", "")
        self.ActionDay = getattr(pDepthMarketData, "ActionDay", "")
        self.UpdateTime = getattr(pDepthMarketData, "UpdateTime", "")
        self.UpdateMillisec = getattr(pDepthMarketData, "UpdateMillisec", 0)
        self.LastPrice = getattr(pDepthMarketData, "LastPrice", 0)
        self.Volume = getattr(pDepthMarketData, "Volume", 0)
        self.PreSettlementPrice = getattr(pDepthMarketData,
                                          "PreSettlementPrice", 0)
        self.PreClosePrice = getattr(pDepthMarketData, "PreClosePrice", 0)
        self.PreOpenInterest = getattr(pDepthMarketData, "PreOpenInterest", 0)
        self.OpenPrice = getattr(pDepthMarketData, "OpenPrice", 0)
        self.HighestPrice = getattr(pDepthMarketData, "HighestPrice", 0)
        self.LowestPrice = getattr(pDepthMarketData, "LowestPrice", 0)
        self.LimitUpPrice = getattr(pDepthMarketData, "LimitUpPrice", 0)
        self.LimitDownPrice = getattr(pDepthMarketData, "LimitDownPrice", 0)
        self.OpenInterest = getattr(pDepthMarketData, "OpenInterest", 0)
        self.Turnover = getattr(pDepthMarketData, "Turnover", 0)
        self.AveragePrice = getattr(pDepthMarketData, "AveragePrice", 0)

        # 买卖盘口数据
        self.BidPrice1 = getattr(pDepthMarketData, "BidPrice1", 0)
        self.BidVolume1 = getattr(pDepthMarketData, "BidVolume1", 0)
        self.AskPrice1 = getattr(pDepthMarketData, "AskPrice1", 0)
        self.AskVolume1 = getattr(pDepthMarketData, "AskVolume1", 0)
        self.BidPrice2 = getattr(pDepthMarketData, "BidPrice2", 0)
        self.BidVolume2 = getattr(pDepthMarketData, "BidVolume2", 0)
        self.AskPrice2 = getattr(pDepthMarketData, "AskPrice2", 0)
        self.AskVolume2 = getattr(pDepthMarketData, "AskVolume2", 0)
        self.BidPrice3 = getattr(pDepthMarketData, "BidPrice3", 0)
        self.BidVolume3 = getattr(pDepthMarketData, "BidVolume3", 0)
        self.AskPrice3 = getattr(pDepthMarketData, "AskPrice3", 0)
        self.AskVolume3 = getattr(pDepthMarketData, "AskVolume3", 0)
        self.BidPrice4 = getattr(pDepthMarketData, "BidPrice4", 0)
        self.BidVolume4 = getattr(pDepthMarketData, "BidVolume4", 0)
        self.AskPrice4 = getattr(pDepthMarketData, "AskPrice4", 0)
        self.AskVolume4 = getattr(pDepthMarketData, "AskVolume4", 0)
        self.BidPrice5 = getattr(pDepthMarketData, "BidPrice5", 0)
        self.BidVolume5 = getattr(pDepthMarketData, "BidVolume5", 0)
        self.AskPrice5 = getattr(pDepthMarketData, "AskPrice5", 0)
        self.AskVolume5 = getattr(pDepthMarketData, "AskVolume5", 0)

    def to_dict(self):
        """
        转换为字典格式
        :return: 行情数据字典
        """
        return {
            "InstrumentID": self.InstrumentID,
            "TradingDay": self.TradingDay,
            "ActionDay": self.ActionDay,
            "UpdateTime": self.UpdateTime,
            "UpdateMillisec": self.UpdateMillisec,
            "LastPrice": self.LastPrice,
            "Volume": self.Volume,
            "PreSettlementPrice": self.PreSettlementPrice,
            "PreClosePrice": self.PreClosePrice,
            "PreOpenInterest": self.PreOpenInterest,
            "OpenPrice": self.OpenPrice,
            "HighestPrice": self.HighestPrice,
            "LowestPrice": self.LowestPrice,
            "LimitUpPrice": self.LimitUpPrice,
            "LimitDownPrice": self.LimitDownPrice,
            "OpenInterest": self.OpenInterest,
            "Turnover": self.Turnover,
            "AveragePrice": self.AveragePrice,
            "BidPrice1": self.BidPrice1,
            "BidVolume1": self.BidVolume1,
            "AskPrice1": self.AskPrice1,
            "AskVolume1": self.AskVolume1,
            "BidPrice2": self.BidPrice2,
            "BidVolume2": self.BidVolume2,
            "AskPrice2": self.AskPrice2,
            "AskVolume2": self.AskVolume2,
            "BidPrice3": self.BidPrice3,
            "BidVolume3": self.BidVolume3,
            "AskPrice3": self.AskPrice3,
            "AskVolume3": self.AskVolume3,
            "BidPrice4": self.BidPrice4,
            "BidVolume4": self.BidVolume4,
            "AskPrice4": self.AskPrice4,
            "AskVolume4": self.AskVolume4,
            "BidPrice5": self.BidPrice5,
            "BidVolume5": self.BidVolume5,
            "AskPrice5": self.AskPrice5,
            "AskVolume5": self.AskVolume5,
        }
