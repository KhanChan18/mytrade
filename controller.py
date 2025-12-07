from openctp_ctp import thostmduserapi as mdapi
from openctp_ctp import thosttraderapi as tdapi
from signal_handler import EXIT_FLAG

# ===================== 公共父类（抽离重复逻辑） =====================
class BaseController:
    """CTP行情/交易控制器公共父类，封装重复的回调逻辑"""
    def __init__(self, conf=None, api=None, request_id=100):
        self.conf = conf  # 配置字典
        self.api = api    # 关联的API实例（MD/Trade）
        self._request_id = request_id
        self.login = False  # 登录状态标记

    @property
    def request_id(self):
        """自增请求ID，公共逻辑"""
        self._request_id += 1
        return self._request_id

    def OnRspError(self, pRspInfo, nRequestID, bIsLast) -> "void":
        """公共的错误回调"""
        errMsg = f"""
        OnRspError >
            RequestID: {nRequestID}
            RespInfo:  {pRspInfo.ErrorID if pRspInfo else 'None'} - {pRspInfo.ErrorMsg if pRspInfo else 'None'}
            is Last?:  {bIsLast}
        """
        print(errMsg)

    def OnHeartBeatWarning(self, nTimeLapse):
        """公共的心跳警告回调"""
        print('HeartBeatWarning, time = {0}'.format(nTimeLapse))

    def OnFrontDisconnected(self, nReason: int) -> "void":
        """公共的前置机断开回调"""
        print(f"OnFrontDisconnected.[nReason={nReason}]")
        EXIT_FLAG.set()

# ===================== 行情控制器（仅保留差异化逻辑） =====================
class MarketDataController(BaseController, mdapi.CThostFtdcMdSpi):
    """行情控制器：继承公共父类 + MD SPI"""
    def __init__(self, conf, api=None):
        # 初始化父类（先BaseController，再MD SPI）
        BaseController.__init__(self, conf=conf, api=api)
        mdapi.CThostFtdcMdSpi.__init__(self)

    def OnFrontConnected(self) -> "void":
        """行情专属的前置机连接成功回调"""
        print("MD OnFrontConnected")
        req = mdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = self.conf['broker_id']
        req.UserID = self.conf['investor_id']
        req.Password = self.conf['password']
        if self.api:
            self.api.ReqUserLogin(req, self.request_id)
        else:
            print("Error: MD API not associated with controller")

    def OnRspUserLogin(
        self,
        pRspUserLogin: 'CThostFtdcRspUserLoginField',
        pRspInfo: 'CThostFtdcRspInfoField',
        nRequestID: 'int',
        bIsLast: 'bool'
    ) -> "void":
        """行情专属的登录响应回调"""
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"MD Login failed. {pRspInfo.ErrorMsg}")
            EXIT_FLAG.set()
            return
        
        print(f"MD Login succeed.{pRspUserLogin.TradingDay}")
        self.login = True
        from config import DEFAULT_SUBSCRIBE_INSTRUMENT
        self.api.SubscribeMarketData([DEFAULT_SUBSCRIBE_INSTRUMENT], self.request_id)

    def OnRtnDepthMarketData(self, pDepthMarketData: 'CThostFtdcDepthMarketDataField') -> "void":
        """行情专属的深度行情推送回调"""
        inst_id = pDepthMarketData.InstrumentID.encode('utf-8') if pDepthMarketData.InstrumentID else "Unknown"
        last_price = pDepthMarketData.LastPrice if pDepthMarketData.LastPrice else 0.0
        volume = pDepthMarketData.Volume if pDepthMarketData.Volume else 0
        print(f"{inst_id} - {last_price} - {volume}")

    def OnRspSubMarketData(
        self,
        pSpecificInstrument: 'CThostFtdcSpecificInstrumentField',
        pRspInfo:            'CThostFtdcRspInfoField',
        nRequestID:          'int',
        bIsLast:             'bool'
    ) -> "void":
        """行情专属的订阅响应回调"""
        inst_id = pSpecificInstrument.InstrumentID.encode('utf-8') if pSpecificInstrument.InstrumentID else "Unknown"
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"MD Subscribe failed. [{inst_id}] {pRspInfo.ErrorMsg}")
            return
        print(f"MD Subscribe succeed.{inst_id}")

# ===================== 交易控制器（仅保留差异化逻辑） =====================
class TradeController(BaseController, tdapi.CThostFtdcTraderSpi):
    """交易控制器：继承公共父类 + Trade SPI"""
    def __init__(self, conf, api=None):
        # 初始化父类（先BaseController，再Trade SPI）
        BaseController.__init__(self, conf=conf, api=api)
        tdapi.CThostFtdcTraderSpi.__init__(self)

    def OnFrontConnected(self):
        """交易专属的前置机连接成功回调（含认证逻辑）"""
        print("Trade OnFrontConnected")
        req = tdapi.CThostFtdcReqAuthenticateField()
        req.BrokerID = self.conf['broker_id']
        req.UserID = self.conf['investor_id']
        req.AuthCode = self.conf['auth_code']
        req.AppID = self.conf['app_id']
        # 调用交易API的认证方法
        self.api.ReqAuthenticate(req, self.request_id)

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """交易专属的认证响应回调"""
        print("Trade OnRspAuthenticate")
        print("nRequestID:", nRequestID, "bIsLast:", bIsLast, "pRspInfo:", pRspInfo)

        if pRspInfo.ErrorID == 0:
            # 认证成功后执行登录
            print('Authentication finished successfully. Then, login.')
            req = tdapi.CThostFtdcReqUserLoginField()
            req.BrokerID = self.conf['broker_id']
            req.UserID = self.conf['investor_id']
            req.Password = self.conf['password']
            self.api.ReqUserLogin(req, self.request_id)
        else:
            print("Trade auth failed:", pRspInfo.ErrorMsg)
            EXIT_FLAG.set()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """交易专属的登录响应回调"""
        print("Trade OnRspUserLogin")
        print("nRequestID:", nRequestID, "bIsLast:", bIsLast, "pRspInfo:", pRspInfo)

        if pRspInfo.ErrorID != 0:
            print("Trade Login failed:", pRspInfo.ErrorMsg)
            EXIT_FLAG.set()
        else:
            print("Trade user login successfully")
            self.login = True
            print("pRspUserLogin:", pRspUserLogin)

    def OnRspQryInvestor(self, pInvestor, pRspInfo, nRequestID, bIsLast):
        """交易专属的查询投资者信息回调"""
        import pdb;pdb.set_trace()
        print("Trade OnRspQryInvestor")
        print("nRequestID:", nRequestID, "bIsLast:", bIsLast, "pRspInfo:", pRspInfo)
        print("pInvestor:", pInvestor)

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """交易专属的查询持仓回调"""
        print("Trade OnRspQryInvestorPosition")
        print("nRequestID:", nRequestID, "bIsLast:", bIsLast, "pRspInfo:", pRspInfo)
        print("pInvestorPosition:", pInvestorPosition)

    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        """交易专属的查询账户回调"""
        print("Trade OnRspQryTradingAccount")
        print("nRequestID:", nRequestID, "bIsLast:", bIsLast, "pRspInfo:", pRspInfo)
        print("pTradingAccount:", pTradingAccount)

# ===================== 行情API封装（无修改） =====================
class MarketDataAPI(mdapi.CThostFtdcMdApi):
    def __init__(self, md_server):
        self.conf = md_server
        super(MarketDataAPI, self).__init__()

# ===================== 交易API封装（补充初始化） =====================
class TradeAPI(tdapi.CThostFtdcTraderApi):
    def __init__(self, trade_server):
        self.conf = trade_server
        super(TradeAPI, self).__init__()