# -*- coding: utf-8 -*-
"""日志模板配置模块"""

# 业务对象打印字段模板（保持不变）
LOG_TEMPLATES = {
    "Order": [
        "UserID", "BrokerID", "InvestorID", "ExchangeID", "InstrumentID",
        "Direction", "CombOffsetFlag", "CombHedgeFlag", "OrderPriceType",
        "LimitPrice", "VolumeTotalOriginal", "FrontID", "SessionID", "OrderRef",
        "TimeCondition", "VolumeCondition", "MinVolume", "RequestID",
        "InvestUnitID", "CurrencyID", "AccountID", "ClientID", "IPAddress",
        "MacAddress", "OrderSysID", "OrderStatus", "StatusMsg", "VolumeTotal",
        "VolumeTraded", "OrderSubmitStatus", "TradingDay", "InsertDate",
        "InsertTime", "UpdateTime", "CancelTime", "UserProductInfo",
        "ActiveUserID", "BrokerOrderSeq", "TraderID", "ParticipantID", "OrderLocalID"
    ],
    "Trade": [
        "BrokerID", "InvestorID", "ExchangeID", "InstrumentID", "Direction",
        "OffsetFlag", "HedgeFlag", "Price", "Volume", "OrderSysID", "OrderRef",
        "TradeID", "TradeDate", "TradeTime", "ClientID", "TradingDay",
        "OrderLocalID", "BrokerOrderSeq", "InvestUnitID", "ParticipantID"
    ],
    "Position": [
        "InstrumentID", "ExchangeID", "HedgeFlag", "PositionDate", "PosiDirection",
        "Position", "YdPosition", "TodayPosition", "UseMargin", "PreMargin",
        "FrozenMargin", "Commission", "FrozenCommission", "CloseProfit",
        "LongFrozen", "ShortFrozen", "PositionCost", "OpenCost", "SettlementPrice"
    ],
    "Instrument": [
        "InstrumentID", "InstrumentName", "ExchangeID", "ProductClass",
        "ProductID", "VolumeMultiple", "PositionType", "PositionDateType",
        "PriceTick", "ExpireDate", "UnderlyingInstrID", "StrikePrice",
        "OptionsType", "MinLimitOrderVolume", "MaxLimitOrderVolume"
    ],
    "SettlementInfoConfirm": [
        "BrokerID", "InvestorID", "ConfirmDate", "ConfirmTime", "CurrencyID"
    ]
}


def get_log_template(template_name):
    """
    获取指定名称的日志模板字段列表
    :param template_name: 模板名称，如 "Order", "Trade"
    :return: 字段列表，如果模板不存在则返回空列表
    """
    return LOG_TEMPLATES.get(template_name, [])


def update_log_template(template_name, fields):
    """
    更新指定名称的日志模板字段列表
    :param template_name: 模板名称，如 "Order", "Trade"
    :param fields: 新的字段列表
    """
    if not isinstance(fields, list):
        raise TypeError("字段列表必须是列表类型")
    LOG_TEMPLATES[template_name] = fields


def add_log_template(template_name, fields):
    """
    添加新的日志模板
    :param template_name: 新模板名称
    :param fields: 字段列表
    """
    if template_name in LOG_TEMPLATES:
        raise KeyError(f"模板 {template_name} 已存在")
    update_log_template(template_name, fields)


def remove_log_template(template_name):
    """
    删除指定名称的日志模板
    :param template_name: 模板名称
    """
    if template_name in LOG_TEMPLATES:
        del LOG_TEMPLATES[template_name]
