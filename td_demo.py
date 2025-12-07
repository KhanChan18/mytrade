"""
核心特点：
1. 移除所有装饰器，恢复最稳定的手动调用模式
2. 保留Req赋值简化（一行赋值）
3. 保留日志模块统一打印
4. 信号量释放改为手动调用logger.release_semaphore()
5. 支持优雅退出（Ctrl+C/杀死进程），安全释放资源
"""
import sys
import time
import threading
import signal
from openctp_ctp import thosttraderapi as tdapi
from ctp_logger import CTPLogger
from ctp_utils import set_req_fields

class TdImpl(tdapi.CThostFtdcTraderSpi):
    def __init__(self, config):
        super().__init__()
        # 基础配置
        self.config = config
        self.TradingDay = ""
        self.OrderRef = 0
        self.is_running = False  # 运行状态标记
        self.exit_event = threading.Event()  # 退出信号
        
        # 初始化API
        self.api = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi()
        self.api.RegisterSpi(self)
        self.api.RegisterFront(config["host"])
        self.api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
        self.api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)

        # 初始化日志器
        self.logger = CTPLogger(log_file="ctp_trade.log", log_level="INFO")

    def set_semaphore(self, semaphore):
        """设置信号量"""
        self.logger.set_semaphore(semaphore)

    def set_exit_event(self, exit_event):
        """设置退出事件"""
        self.exit_event = exit_event

    def Run(self):
        """启动API"""
        self.is_running = True
        self.api.Init()

    def stop(self):
        """优雅停止"""
        if not self.is_running:
            return
        
        self.logger.info("TdImpl", "开始停止CTP API...")
        self.is_running = False
        self.exit_event.set()  # 触发退出信号
        
        # 安全释放API资源
        try:
            self.api.RegisterFront("")  # 清空前置机
            self.api.Release()
            self.logger.info("TdImpl", "CTP API已安全释放")
        except Exception as e:
            self.logger.error("TdImpl", f"释放API失败: {e}")

    # ========== 核心回调函数（手动释放信号量） ==========
    def OnFrontConnected(self):
        """前置机连接成功"""
        if not self.is_running:
            return
        self.logger.info("OnFrontConnected", "前置机连接成功，开始认证")
        
        # 发送认证请求
        req = tdapi.CThostFtdcReqAuthenticateField()
        set_req_fields(req, {
            "BrokerID": self.config["broker"],
            "UserID": self.config["user"],
            "AppID": self.config["appid"],
            "AuthCode": self.config["authcode"]
        })
        self.api.ReqAuthenticate(req, 0)

    def OnFrontDisconnected(self, nReason):
        """前置机断开"""
        self.logger.error("OnFrontDisconnected", f"前置机断开，原因码: {nReason}")
        if self.is_running:
            self.exit_event.set()  # 断开连接时触发退出

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """认证响应"""
        if not self.is_running:
            return
        
        if self.logger.print_error("OnRspAuthenticate", pRspInfo):
            self.exit_event.set()
            exit(-1)
        
        self.logger.info("OnRspAuthenticate", "认证成功，开始登录")
        
        # 发送登录请求
        req = tdapi.CThostFtdcReqUserLoginField()
        set_req_fields(req, {
            "BrokerID": self.config["broker"],
            "UserID": self.config["user"],
            "Password": self.config["password"]
        })
        self.api.ReqUserLogin(req, 0)
        
        # 手动释放信号量
        self.logger.release_semaphore(bIsLast)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录响应"""
        if not self.is_running:
            return
        
        if self.logger.print_error("OnRspUserLogin", pRspInfo):
            self.exit_event.set()
            exit(-1)
        
        self.logger.info("OnRspUserLogin", 
            f"登录成功 | 交易日: {pRspUserLogin.TradingDay} | 最大报单引用: {pRspUserLogin.MaxOrderRef}"
        )
        self.TradingDay = pRspUserLogin.TradingDay
        self.OrderRef = 1
        
        # 手动释放信号量
        self.logger.release_semaphore(bIsLast)

    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """查询合约响应"""
        if not self.is_running:
            return
        
        if not self.logger.print_error("OnRspQryInstrument", pRspInfo) and pInstrument:
            self.logger.print_object("OnRspQryInstrument", pInstrument, "Instrument")
        
        # 手动释放信号量
        self.logger.release_semaphore(bIsLast)

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """查询持仓响应"""
        if not self.is_running:
            return
        
        if not self.logger.print_error("OnRspQryPosition", pRspInfo) and pInvestorPosition:
            self.logger.print_object("OnRspQryPosition", pInvestorPosition, "Position")
        
        # 手动释放信号量
        self.logger.release_semaphore(bIsLast)

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """下单响应"""
        if not self.is_running:
            return
        
        if self.logger.print_error("OnRspOrderInsert", pRspInfo):
            self.logger.error("OnRspOrderInsert", f"下单失败 | {pRspInfo.ErrorMsg}")
        else:
            self.logger.info("OnRspOrderInsert", f"下单请求已受理 | 报单引用: {pRspInfo.ErrorMsg}")
        
        # 手动释放信号量
        self.logger.release_semaphore(bIsLast)


    def OnRtnOrder(self, pOrder):
        """订单回报"""
        if self.is_running:
            self.logger.print_object("OnRtnOrder", pOrder, "Order")

    def OnRtnTrade(self, pTrade):
        """成交回报"""
        if self.is_running:
            self.logger.print_object("OnRtnTrade", pTrade, "Trade")

    # ========== 业务方法（Req赋值简化） ==========
    def QryInstrument(self, exchangeid="", productid="", instrumentid=""):
        """查询合约"""
        if not self.is_running:
            return
        
        self.logger.info("QryInstrument", f"开始查询合约 | 交易所: {exchangeid} | 合约: {instrumentid}")
        req = tdapi.CThostFtdcQryInstrumentField()
        set_req_fields(req, {
            "ExchangeID": exchangeid,
            "ProductID": productid,
            "InstrumentID": instrumentid
        })
        self.api.ReqQryInstrument(req, 0)

    def QryPosition(self, instrumentid=""):
        """查询持仓"""
        if not self.is_running:
            return
        
        self.logger.info("QryPosition", f"开始查询持仓 | 合约: {instrumentid}")
        req = tdapi.CThostFtdcQryInvestorPositionField()
        set_req_fields(req, {
            "BrokerID": self.config["broker"],
            "InvestorID": self.config["user"],
            "InstrumentID": instrumentid
        })
        ret = self.api.ReqQryInvestorPosition(req, 0)
        self.logger.info("QryPosition", f"查询持仓结果 | 返回: {ret}")

    def OrderInsert(self, order_params):
        """
        下单方法（简化版）
        :param order_params: 下单参数字典
        """
        if not self.is_running:
            self.logger.warning("OrderInsert", "程序已停止，拒绝下单请求")
            return
        
        self.logger.info("OrderInsert", f"开始下单 | 参数: {order_params}")
        
        req = tdapi.CThostFtdcInputOrderField()
        # 基础固定字段
        base_fields = {
            "BrokerID": self.config["broker"],
            "InvestorID": self.config["user"],
            "CombHedgeFlag": tdapi.THOST_FTDC_HF_Speculation,
            "ForceCloseReason": tdapi.THOST_FTDC_FCC_NotForceClose,
            "ContingentCondition": tdapi.THOST_FTDC_CC_Immediately,
            "OrderRef": str(self.OrderRef)
        }
        
        # 合并基础字段和业务字段
        all_fields = {**base_fields, **order_params}
        set_req_fields(req, all_fields)
        from pprint import pprint as pp
        pp(req)
        pp(all_fields)
        # 发送下单请求
        ret = self.api.ReqOrderInsert(req, 0)
        self.logger.info("OrderInsert", f"下单请求已发送 | 报单结果: {ret}")
        
        # 更新报单引用
        self.OrderRef += 1

# ========== 信号处理器（捕获终止信号） ==========
def signal_handler(signum, frame, exit_event, td_impl, logger):
    """
    处理SIGINT(Ctrl+C)和SIGTERM(杀死进程)信号
    """
    signal_name = signal.Signals(signum).name
    logger.info("信号处理器", f"捕获到{signal_name}信号，开始优雅退出...")
    
    # 设置退出事件
    exit_event.set()
    
    # 停止交易实例
    if td_impl:
        td_impl.stop()

# ========== 主执行逻辑 ==========
if __name__ == "__main__":
    # 配置参数（根据实际情况修改）
    config = {
        "user": '250881',
        "password": 'chh931118CHH!@#',
        "broker": '9999',
        "appid": 'simnow_client_test',
        "authcode": '0000000000000000',
        "host": 'tcp://182.254.243.31:40001',
        "instrument_id": "p2605"
    }

    # 初始化核心控制对象
    exit_event = threading.Event()  # 退出事件
    semaphore = threading.Semaphore(0)  # 同步信号量

    # 初始化交易实例
    tdImpl = TdImpl(config)
    tdImpl.set_semaphore(semaphore)
    tdImpl.set_exit_event(exit_event)

    # 注册信号处理器（支持Ctrl+C和kill命令）
    main_logger = tdImpl.logger
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, exit_event, tdImpl, main_logger))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, exit_event, tdImpl, main_logger))

    try:
        # 启动API
        main_logger.info("主程序", "启动CTP API...")
        tdImpl.Run()

        # 等待认证+登录完成
        main_logger.info("主程序", "等待登录完成...")
        # 设置超时，防止死锁
        login_success = True
        try:
            # 等待认证响应（10秒超时）
            if not semaphore.acquire(timeout=10):
                raise TimeoutError("认证响应超时")
            # 等待登录响应（10秒超时）
            if not semaphore.acquire(timeout=10):
                raise TimeoutError("登录响应超时")
        except TimeoutError as e:
            main_logger.error("主程序", f"登录失败: {e}")
            login_success = False
            exit_event.set()
        
        if login_success:
            main_logger.info("主程序", "登录流程完成")

            # ========== 执行业务操作 ==========
            # 1. 查询合约
            tdImpl.QryInstrument(exchangeid="DCE", instrumentid=config["instrument_id"])
            if semaphore.acquire(timeout=5):  # 5秒超时
                time.sleep(0.5)
            else:
                main_logger.warning("主程序", "查询合约超时")

            # 2. 查询持仓
            tdImpl.QryPosition(instrumentid=config["instrument_id"])
            if semaphore.acquire(timeout=5):  # 5秒超时
                time.sleep(0.5)
            else:
                main_logger.warning("主程序", "查询持仓超时")

            # 3. 下单（示例：买入开仓）
            order_params = {
                "ExchangeID": "DCE",
                "InstrumentID": config["instrument_id"],
                "Direction": tdapi.THOST_FTDC_D_Buy,          # 买入
                "CombOffsetFlag": tdapi.THOST_FTDC_OF_Open,   # 开仓
                "OrderPriceType": tdapi.THOST_FTDC_OPT_LimitPrice,  # 限价单
                "LimitPrice": "8780",
                "VolumeTotalOriginal": 1,
                "TimeCondition": tdapi.THOST_FTDC_TC_GFD,     # 当日有效
                "VolumeCondition": tdapi.THOST_FTDC_VC_AV,    # 任意成交量
                "MinVolume": 1,
                #
                "IsAutoSpeed": 0,
                "IsSwapOrder": 0,
                # "ContingentCondition": "",
                "ForceCloseReason": tdapi.THOST_FTDC_FCC_NotForceClose,
                "StopPrice": "8700",

            }
            tdImpl.OrderInsert(order_params)
            if semaphore.acquire(timeout=5):  # 5秒超时
                time.sleep(0.5)
            else:
                main_logger.warning("主程序", "下单响应超时")

            # ========== 保持运行（可接收回报） ==========
            main_logger.info("主程序", "业务操作完成，进入持续运行状态（按Ctrl+C退出）...")
            # 等待退出事件，替代死循环
            while not exit_event.is_set():
                time.sleep(0.1)

    except Exception as e:
        main_logger.error("主程序", f"运行异常: {e}", exc_info=True)
    finally:
        # 最终资源释放
        main_logger.info("主程序", "执行最终资源清理...")
        
        # 停止交易实例
        tdImpl.stop()
        
        # 清理信号量
        try:
            # 释放所有可能的信号量，防止死锁
            while semaphore._value < 0:
                semaphore.release()
        except:
            pass
        
        main_logger.info("主程序", "程序已优雅退出，所有资源已释放")
        sys.exit(0)