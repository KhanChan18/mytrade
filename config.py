# -*- coding: utf-8 -*-
"""CTP配置管理模块（适配目录配置+自动创建文件夹，默认配置文件CONF.yml）"""
import ctypes
import yaml
import os
import platform
import sys
from datetime import datetime
from openctp_ctp import thosttraderapi as tdapi

# ===================== 核心配置读取（适配默认文件名 CONF.yml） =====================
def load_config(yaml_path="CONF.yml"):
    """
    加载YAML配置文件，适配CTP_SERVER/APP_CONFIG层级
    默认读取根目录CONF.yml，再读配置文件夹内的CONF.yml
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"配置文件不存在: {yaml_path}")
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)
    
    # 提取各节点配置
    APP_CONFIG = raw_config.get("APP_CONFIG", {})
    CONF_LIST = raw_config.get("CTP_SERVER", {})
    
    return APP_CONFIG, CONF_LIST

# 第一步：先加载根目录的默认配置文件（CONF.yml）
try:
    APP_CONFIG, CONF_LIST = load_config("CONF.yml")
except FileNotFoundError as e:
    # 备用：加载配置文件夹内的CONF.yml（如果根目录文件不存在）
    backup_config_path = os.path.join("./mytrade/conf", "CONF.yml")
    if os.path.exists(backup_config_path):
        APP_CONFIG, CONF_LIST = load_config(backup_config_path)
    else:
        raise FileNotFoundError(f"默认配置文件 CONF.yml 不存在（根目录/配置文件夹均未找到）") from e

# Transform those required configurations into constants
# This code need to be optimized later.
IS_PRODUCTION_MODE = APP_CONFIG.get("is_production_mode", True)

# ===================== 目录路径配置（自动创建文件夹） =====================
# 根目录（默认./mytrade，从APP_CONFIG读取）
ROOT_PATH = APP_CONFIG.get("root_path", "./mytrade")

# 子文件夹名称（简短命名，从APP_CONFIG读取）
SUB_FOLDERS = APP_CONFIG.get("sub_folders", {})
LOG_FOLDER = SUB_FOLDERS.get("log", "logs")
CONFIG_FOLDER = SUB_FOLDERS.get("config", "conf")
STREAM_FOLDER = SUB_FOLDERS.get("stream", "streams")

# 最终路径（拼接）
LOG_PATH = os.path.join(ROOT_PATH, LOG_FOLDER)
CONFIG_PATH = os.path.join(ROOT_PATH, CONFIG_FOLDER)
STREAM_PATH = os.path.join(ROOT_PATH, STREAM_FOLDER)

# 自动创建目录（递归创建，不存在则新建）
def create_folders():
    for folder in [ROOT_PATH, LOG_PATH, CONFIG_PATH, STREAM_PATH]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"创建文件夹: {folder}")

# 第二步：执行目录创建（依赖APP_CONFIG加载完成）
create_folders()

# ===================== 动态文件路径（按日期命名） =====================
# 今日日期（YYYYMMDD）
TODAY = datetime.now().strftime("%Y%m%d")

# 日志文件路径（按日期命名，如 ./mytrade/logs/20251207_ctp.log）
LOG_FILE = os.path.join(LOG_PATH, f"{TODAY}_ctp.log")

# 配置文件路径（固定为 CONF.yml，存储到配置文件夹）
CONF_YML_PATH = os.path.join(CONFIG_PATH, "CONF.yml")

# 流文件基础路径（如 ./mytrade/streams/20251207_）
STREAM_BASE_PATH = os.path.join(STREAM_PATH, f"{TODAY}_")


# ===================== 快捷获取配置（兼容原逻辑） =====================
def get_config(platform, env):
    """
    兼容原get_config逻辑，精准返回指定平台+环境的配置
    :param platform: ZXJT/SIMNOW
    :param env: verifying/simulation/simulation_0等
    """
    try:
        return CONF_LIST[platform][env]
    except KeyError as e:
        raise ValueError(f"配置不存在：platform={platform}, env={env}，错误键：{e}") from e

# ===================== 全局常量 =====================

# 下单默认参数
DEFAULT_INSTRUMENT_STR = "rb2601"  # 默认合约代码
ORDER_PARAMS_DEFAULT = {
    "ExchangeID": "SHFE",
    "InstrumentID": DEFAULT_INSTRUMENT_STR,
    "Direction": tdapi.THOST_FTDC_D_Buy,
    "CombOffsetFlag": tdapi.THOST_FTDC_OF_Open,
    "OrderPriceType": tdapi.THOST_FTDC_OPT_LimitPrice,
    "LimitPrice": 13633,
    "VolumeTotalOriginal": 1,
    "TimeCondition": tdapi.THOST_FTDC_TC_GFD,
    "VolumeCondition": tdapi.THOST_FTDC_VC_AV,
    "MinVolume": 1,
    "IsAutoSpeed": 0,
    "IsSwapOrder": 0,
    "ForceCloseReason": tdapi.THOST_FTDC_FCC_NotForceClose,
    "StopPrice": 13300,
}

# 日志配置（动态路径）
LOG_CONFIG = {
    "log_file": LOG_FILE,       # 按日期命名的日志文件
    "log_level": APP_CONFIG.get("log_level", "INFO")        # 日志级别：DEBUG/INFO/ERROR
}

# ===================== 系统编码适配 =====================
def setup_system_encoding():
    if platform.system() == "Windows":
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass

setup_system_encoding()

# ===================== 额外工具函数（可选） =====================
def get_stream_file_path(filename):
    """获取流文件最终路径（如 ./mytrade/streams/20251207_xxx.stream）"""
    return f"{STREAM_BASE_PATH}{filename}"

# ===================== 配置文件同步（确保CONF.yml在配置文件夹） =====================
def sync_config_to_conf_folder():
    """将根目录CONF.yml同步到配置文件夹（确保配置文件夹有最新版本）"""
    if os.path.exists("CONF.yml") and not os.path.exists(CONF_YML_PATH):
        import shutil
        shutil.copy("CONF.yml", CONF_YML_PATH)
        print(f"配置文件已同步到: {CONF_YML_PATH}")
    elif os.path.exists("CONF.yml") and os.path.exists(CONF_YML_PATH):
        # 可选：覆盖更新（如需保持配置文件夹版本最新，取消注释）
        # shutil.copy("CONF.yml", CONF_YML_PATH)
        pass

# 执行配置文件同步
sync_config_to_conf_folder()
