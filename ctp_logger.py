# ctp_logger.py
from datetime import datetime

class CTPLogger:
    # 业务对象打印字段模板
    PRINT_TEMPLATES = {
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

    def __init__(self, log_file=None, log_level="INFO"):
        self._semaphore = None
        self._log_file = log_file
        self._log_level = log_level  # DEBUG/INFO/ERROR

    def set_semaphore(self, semaphore):
        """设置信号量"""
        self._semaphore = semaphore

    def get_timestamp(self):
        """获取格式化时间戳（精确到毫秒）"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def print_log(self, level, prefix, content):
        """统一日志打印（支持文件+控制台）"""
        if level not in ["DEBUG", "INFO", "ERROR"]:
            level = "INFO"
        
        # 日志级别过滤
        level_priority = {"DEBUG": 0, "INFO": 1, "ERROR": 2}
        if level_priority[level] < level_priority[self._log_level]:
            return
        
        log_str = f"[{self.get_timestamp()}] [{level}] {prefix}: {content}"
        print(log_str)
        
        # 写入文件
        if self._log_file:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(log_str + "\n")
            except Exception as e:
                print(f"日志写入失败: {e}")

    def print_error(self, func_name, pRspInfo):
        """通用错误打印"""
        if pRspInfo and hasattr(pRspInfo, 'ErrorID') and pRspInfo.ErrorID != 0:
            self.print_log("ERROR", func_name, f"失败: {pRspInfo.ErrorMsg}")
            return True
        return False

    def print_object(self, prefix, obj, template_name):
        """通用对象打印"""
        if not obj:
            return
        field_list = self.PRINT_TEMPLATES.get(template_name, [])
        fields_str = " ".join([f"{k}={getattr(obj, k, 'N/A')}" for k in field_list])
        self.print_log("INFO", prefix, fields_str)

    def release_semaphore(self, bIsLast):
        """手动释放信号量（核心：移除装饰器后恢复手动调用）"""
        if self._semaphore and bIsLast:
            try:
                self._semaphore.release()
                self.print_log("DEBUG", "Semaphore", "信号量已释放")
            except Exception as e:
                self.print_log("ERROR", "Semaphore", f"信号量释放失败: {e}")

    # 快捷方法
    def debug(self, prefix, content):
        self.print_log("DEBUG", prefix, content)

    def info(self, prefix, content):
        self.print_log("INFO", prefix, content)

    def error(self, prefix, content):
        self.print_log("ERROR", prefix, content)