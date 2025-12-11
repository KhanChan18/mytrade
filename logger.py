from datetime import datetime
import inspect  # 用于获取调用栈信息

class CTPLogger:
    # 业务对象打印字段模板（保持不变）
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
        """
        初始化日志器
        :param log_file: 日志文件路径（None则仅控制台输出）
        :param log_level: 日志等级，可选 DEBUG/INFO/ERROR，默认 INFO
        """
        self._semaphore = None
        self._log_file = log_file
        # 日志等级校验，非法值默认INFO
        self._log_level = log_level.upper() if log_level.upper() in ["DEBUG", "INFO", "ERROR"] else "INFO"

    def set_semaphore(self, semaphore):
        """设置信号量"""
        self._semaphore = semaphore

    def get_timestamp(self):
        """获取格式化时间戳（精确到毫秒）"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def get_caller_info(self):
        """获取调用日志的代码位置信息（文件+行号+函数名）"""
        try:
            # 调用栈层级：适配「业务代码→快捷方法→print_log→get_caller_info」
            frame = inspect.stack()[3]
            file_name = frame.filename
            # 简化文件名（跨平台兼容Windows/Linux）
            short_file = file_name.split("/")[-1] if "/" in file_name else file_name.split("\\")[-1]
            line_no = frame.lineno  # 行号
            func_name = frame.function  # 调用函数名
            return f"{short_file}:{line_no}({func_name})"
        except Exception:
            # 降级处理：兼容栈层级异常的情况
            frame = inspect.stack()[2]
            file_name = frame.filename
            short_file = file_name.split("/")[-1] if "/" in file_name else file_name.split("\\")[-1]
            line_no = frame.lineno
            func_name = frame.function
            return f"{short_file}:{line_no}({func_name})"

    def print_log(self, level, prefix, content):
        """统一日志打印（所有等级都输出行号）"""
        # 日志等级标准化
        level = level.upper() if level.upper() in ["DEBUG", "INFO", "ERROR"] else "INFO"
        
        # 日志级别过滤：低于设置等级的日志不输出
        level_priority = {"DEBUG": 0, "INFO": 1, "ERROR": 2}
        if level_priority[level] < level_priority[self._log_level]:
            return
        
        # 构建日志字符串：所有等级都包含行号
        timestamp = self.get_timestamp()
        caller_info = self.get_caller_info()
        log_str = f"[{timestamp}] [{level}] [{caller_info}] {prefix}: {content}"
        
        # 控制台输出
        print(log_str)
        
        # 写入文件（保持原有逻辑）
        if self._log_file:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(log_str + "\n")
            except Exception as e:
                print(f"日志写入失败: {e}")

    def print_error(self, func_name, pRspInfo):
        """通用错误打印（带行号）"""
        if pRspInfo and hasattr(pRspInfo, 'ErrorID') and pRspInfo.ErrorID != 0:
            self.print_log("ERROR", func_name, f"失败: {pRspInfo.ErrorMsg}")
            return True
        return False

    def print_object(self, prefix, obj, template_name):
        """通用对象打印（带行号）"""
        if not obj:
            return
        field_list = self.PRINT_TEMPLATES.get(template_name, [])
        fields_str = " ".join([f"{k}={getattr(obj, k, 'N/A')}" for k in field_list])
        self.print_log("INFO", prefix, fields_str)

    def release_semaphore(self, bIsLast):
        """手动释放信号量（带行号）"""
        if self._semaphore and bIsLast:
            try:
                self._semaphore.release()
                self.print_log("DEBUG", "Semaphore", "信号量已释放")
            except Exception as e:
                self.print_log("ERROR", "Semaphore", f"信号量释放失败: {e}")

    # 快捷方法（保持不变）
    def debug(self, prefix, content):
        self.print_log("DEBUG", prefix, content)

    def info(self, prefix, content):
        self.print_log("INFO", prefix, content)

    def error(self, prefix, content):
        self.print_log("ERROR", prefix, content)