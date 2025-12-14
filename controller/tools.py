import yaml
import datetime
import os
from typing import List, Tuple, Dict


def load_futures_config(config_path: str = "instrument.yml") -> Dict:
    """
    读取期货交易所YAML配置文件
    """
    try:
        # 如果是相对路径，先尝试在项目根目录查找，再尝试在当前目录查找
        if not os.path.isabs(config_path):
            # 尝试项目根目录（instrument.yml现在的位置）
            project_root = os.path.dirname(os.path.dirname(__file__))
            project_config_path = os.path.join(project_root, config_path)
            if os.path.exists(project_config_path):
                config_path = project_config_path
            else:
                # 尝试tools.py所在目录（旧位置）
                current_dir = os.path.dirname(__file__)
                config_path = os.path.join(current_dir, config_path)

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    except Exception as e:
        raise ValueError(f"配置文件读取失败：{str(e)}")


def calculate_contract_months() -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    计算投机/交割合约月份（从根源区分，无事后过滤）
    返回：(投机合约月份, 交割合约月份)
    规则：
    - 交割月：当前月（如2025年12月=2512），仅交割功能
    - 投机月：交割月的下一月（如2025年12月→2601），可正常投机
    """
    today = datetime.date.today()
    curr_year, curr_month = today.year, today.month

    # 交割合约月份 = 当前月
    delivery_year, delivery_month = curr_year, curr_month

    # 投机合约月份 = 交割月的下一月（跨年度自动处理）
    speculation_year, speculation_month = (
        curr_year + 1, 1) if curr_month == 12 else (curr_year, curr_month + 1)

    return (speculation_year, speculation_month), (delivery_year, delivery_month)


def generate_contract_dict(config_path: str = "instrument.yml") -> Dict[str, List[str]]:
    """
    生成包含投机/交割/全体合约的字典
    返回格式：
    {
        'speculation': [可投机合约列表],
        'delivery': [交割合约列表],
        'all': [全体合约列表（投机+交割）]
    }
    """
    # 1. 读取配置 + 计算两类合约月份
    config = load_futures_config(config_path)
    (spec_year, spec_month), (deliv_year, deliv_month) = calculate_contract_months()

    # 2. 生成月份后缀
    spec_ym = f"{str(spec_year)[-2:]}{spec_month:02d}"  # 投机月后缀（如2601）
    deliv_ym = f"{str(deliv_year)[-2:]}{deliv_month:02d}"  # 交割月后缀（如2512）

    # 3. 根源生成三类合约（无无效合约，无需过滤）
    speculation_contracts = []  # 投机合约
    delivery_contracts = []     # 交割合约
    all_contracts = []          # 全体合约

    for exch_info in config.values():
        if "products" not in exch_info:
            continue
        for product in exch_info["products"]:
            pure_abbr = product.split("#")[0].strip()
            if pure_abbr:
                # 生成单品种的投机/交割合约
                spec_contract = f"{pure_abbr}{spec_ym}"
                deliv_contract = f"{pure_abbr}{deliv_ym}"

                # 分别追加到对应列表
                speculation_contracts.append(spec_contract)
                delivery_contracts.append(deliv_contract)
                all_contracts.extend(
                    [spec_contract, deliv_contract])  # 全体合约=投机+交割

    # 4. 返回最终字典（含三个字段）
    return {
        "speculation": speculation_contracts,
        "delivery": delivery_contracts,
        "all": all_contracts
    }


def generate_contract_exchange_map(config_path: str = "instrument.yml") -> Dict[str, str]:
    """
    生成合约代码到交易所的映射字典
    返回格式：
    {
        'rb2512': 'SHFE',
        'cu2512': 'SHFE',
        'a2512': 'DCE',
        ...
    }
    """
    try:
        # 1. 读取配置 + 计算两类合约月份
        print(f"Trying to load config from: {config_path}")
        config = load_futures_config(config_path)
        print(f"Config loaded successfully, keys: {list(config.keys())}")
        (spec_year, spec_month), (deliv_year,
                                  deliv_month) = calculate_contract_months()

        # 2. 生成月份后缀
        spec_ym = f"{str(spec_year)[-2:]}{spec_month:02d}"  # 投机月后缀（如2601）
        deliv_ym = f"{str(deliv_year)[-2:]}{deliv_month:02d}"  # 交割月后缀（如2512）
        print(f"Generated month suffixes: spec={spec_ym}, deliv={deliv_ym}")

        # 3. 生成合约-交易所映射
        contract_exchange_map = {}

        for exch_code, exch_info in config.items():
            if "products" not in exch_info:
                print(f"Exchange {exch_code} has no products")
                continue
            for product in exch_info["products"]:
                pure_abbr = product.split("#")[0].strip()
                if pure_abbr:
                    # 生成单品种的投机/交割合约
                    spec_contract = f"{pure_abbr}{spec_ym}"
                    deliv_contract = f"{pure_abbr}{deliv_ym}"

                    # 将合约映射到对应的交易所
                    contract_exchange_map[spec_contract] = exch_code
                    contract_exchange_map[deliv_contract] = exch_code

        print(
            f"Generated contract_exchange_map with {len(contract_exchange_map)} entries")
        return contract_exchange_map
    except Exception as e:
        print(f"Error in generate_contract_exchange_map: {e}")
        return {}


# 全局合约-交易所映射，在应用启动时初始化
contract_exchange_map = None

# 初始化全局合约-交易所映射


def init_contract_exchange_map(config_path: str = "instrument.yml") -> Dict[str, str]:
    """
    初始化全局合约-交易所映射
    """
    global contract_exchange_map
    contract_exchange_map = generate_contract_exchange_map(config_path)
    return contract_exchange_map


# 示例调用
if __name__ == "__main__":
    contract_dict = generate_contract_dict()
    contract_exchange_map = generate_contract_exchange_map()

    print("=== 交割合约列表（当前月，仅交割功能）===")
    print(contract_dict["delivery"][:5])  # 仅打印前5个示例

    print("\n=== 投机合约列表（下一月，可正常投机）===")
    print(contract_dict["speculation"][:5])  # 仅打印前5个示例

    print("\n=== 全体合约列表（投机+交割）===")
    print(contract_dict["all"][:10])  # 仅打印前10个示例

    print("\n=== 合约-交易所映射示例 ===")
    for contract, exch in list(contract_exchange_map.items())[:10]:
        print(f"{contract}: {exch}")
