# config.py
# CTP服务器配置列表
CONF_LIST = {
    "ZXJT": {
        "verifying": {
            'investor_id':  '12345678',
            'password':     'CS123456',
            'broker_id':    '6666',
            'app_id':       'client_syldavia_0.0.1',
            'auth_code':    'FSH2IH17WDVB3S5J',
            'md_server':    'tcp://61.186.254.131:42213',
            'trade_server': 'tcp://61.186.254.131:42205',
        },
        "simulation": {
            'investor_id':  '50004711',
            'password':     'P12345678',
            'broker_id':    '6666',
            'app_id':       'client_syldavia_0.0.1',
            'auth_code':    'FSH2IH17WDVB3S5J',
            'md_server':    'tcp://61.186.254.137:33435',
            'trade_server': 'tcp://61.186.254.137:33433',
        },
    },
    "SIMNOW": {
        "simulation_0": {
            "investor_id": "250881",
            "password": "chh931118CHH!@#",
            "broker_id": "9999",
            "app_id": "simnow_client_test",
            "auth_code": "0000000000000000",
            "md_server": "tcp://182.254.243.31:30011",
            "trader_server": "tcp://182.254.243.31:30001",
        },
        "simulation_1": {
            "investor_id": "250881",
            "password": "chh931118CHH!@#",
            "broker_id": "9999",
            "app_id": "simnow_client_test",
            "auth_code": "0000000000000000",
            "md_server": "tcp://182.254.243.31:30012",
            "trader_server": "tcp://182.254.243.31:30002",
        },
        "simulation_2": {
            "investor_id": "250881",
            "password": "chh931118CHH!@#",
            "broker_id": "9999",
            "app_id": "simnow_client_test",
            "auth_code": "0000000000000000",
            "md_server": "tcp://182.254.243.31:30013",
            "trader_server": "tcp://182.254.243.31:30003",
        },
        "simulation_7*24": {
            "investor_id": "250881",
            "password": "chh931118CHH!@#",
            "broker_id": "9999",
            "app_id": "simnow_client_test",
            "auth_code": "0000000000000000",
            "md_server": "tcp://182.254.243.31:40011",
            "trader_server": "tcp://182.254.243.31:40001",
        },
    }
}

# 通用配置
DEFAULT_SUBSCRIBE_INSTRUMENT = b"ag2602"