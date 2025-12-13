# -*- coding: utf-8 -*-
"""CTP配置管理模块（适配目录配置+自动创建文件夹，默认配置文件CONF.yml）"""
import yaml
import os
import platform
import sys
from datetime import datetime

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
    CTP_SERVER = raw_config.get("CTP_SERVER", {})
    
    return APP_CONFIG, CTP_SERVER

# 加载配置文件
try:
    APP_CONFIG, CTP_SERVER = load_config("CONF.yml")
except FileNotFoundError as e:
    # 备用：加载配置文件夹内的CONF.yml（如果根目录文件不存在）
    backup_config_path = os.path.join("./mytrade/conf", "CONF.yml")
    if os.path.exists(backup_config_path):
        APP_CONFIG, CTP_SERVER = load_config(backup_config_path)
    else:
        raise FileNotFoundError(f"默认配置文件 CONF.yml 不存在（根目录/配置文件夹均未找到）") from e

# ===================== 核心配置常量 =====================
IS_PRODUCTION_MODE = APP_CONFIG.get("is_production_mode", True)
LOG_LEVEL = APP_CONFIG.get("log_level", "INFO")

# ===================== 目录路径配置（自动创建文件夹） =====================
# 根目录（默认./mytrade，从APP_CONFIG读取）
ROOT_PATH = os.path.abspath(APP_CONFIG.get("root_path", "mytrade"))

# 子文件夹名称（简短命名，从APP_CONFIG读取）
SUB_FOLDERS = APP_CONFIG.get("sub_folders", {})
LOG_FOLDER = SUB_FOLDERS.get("log", "logs")
CONFIG_FOLDER = SUB_FOLDERS.get("config", "conf")
STREAM_FOLDER = SUB_FOLDERS.get("stream", "streams")
DB_FOLDER = SUB_FOLDERS.get("db", "db")

# 最终路径（拼接）
LOG_PATH = os.path.join(ROOT_PATH, LOG_FOLDER)
CONFIG_PATH = os.path.join(ROOT_PATH, CONFIG_FOLDER)
STREAM_PATH = os.path.join(ROOT_PATH, STREAM_FOLDER)

# 确保STREAM_PATH以目录分隔符结尾，以便CTP API正确识别为目录
if not STREAM_PATH.endswith(os.path.sep):
    STREAM_PATH += os.path.sep

# 自动创建目录（递归创建，不存在则新建）
def create_folders():
    for folder in [ROOT_PATH, LOG_PATH, CONFIG_PATH, STREAM_PATH]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"创建文件夹: {folder}")

# 执行目录创建
create_folders()

# ===================== 动态文件路径（按日期命名） =====================
# 今日日期（YYYYMMDD）
TODAY = datetime.now().strftime("%Y%m%d")

# 日志文件路径（按日期命名，如 ./mytrade/logs/20251207_ctp.log）
LOG_FILE = os.path.join(LOG_PATH, f"{TODAY}_ctp.log")

# 流文件基础路径（如 ./mytrade/streams/20251207_）
STREAM_BASE_PATH = os.path.join(STREAM_PATH, f"{TODAY}_")

# ===================== 快捷获取配置 =====================
def get_server_config(platform, env):
    """
    获取指定平台+环境的服务器配置
    :param platform: ZXJT/SIMNOW/OPENCTP
    :param env: verifying/simulation/simulation_0/simulation_7*24等
    """
    try:
        return CTP_SERVER[platform][env]
    except KeyError as e:
        raise ValueError(f"服务器配置不存在：platform={platform}, env={env}，错误键：{e}") from e

# ===================== 日志配置 =====================
LOG_CONFIG = {
    "log_file": LOG_FILE,       # 按日期命名的日志文件
    "log_level": LOG_LEVEL      # 日志级别：DEBUG/INFO/ERROR
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

# ===================== 数据收集配置 =====================
# 从APP_CONFIG中获取数据收集配置
DATA_COLLECTION_CONFIG = APP_CONFIG.get("data_collection", {})

# 数据库类型（默认HDF5）
DB_TYPE = DATA_COLLECTION_CONFIG.get("db_type", "HDF5")

# 缓冲区大小（默认128）
BUFFER_SIZE = DATA_COLLECTION_CONFIG.get("buffer_size", 128)

# 数据收集器进程数量（默认1）
COLLECTOR_COUNT = DATA_COLLECTION_CONFIG.get("collector_count", 1)

# 数据库存储路径
DB_PATH = os.path.join(ROOT_PATH, DATA_COLLECTION_CONFIG.get("db_path", DB_FOLDER))

# 创建数据库目录
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)
    print(f"创建文件夹: {DB_PATH}")

# ===================== 工具函数 =====================
def get_stream_file_path(filename):
    """获取流文件最终路径（如 ./mytrade/streams/20251207_xxx.stream）"""
    return f"{STREAM_BASE_PATH}{filename}"
