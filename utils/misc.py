# -*- coding: utf-8 -*-
"""CTP工具函数（仅保留核心）"""


def set_req_fields(req_obj, field_dict):
    """批量设置CTP请求结构体字段"""
    for field, value in field_dict.items():
        if hasattr(req_obj, field):
            # 字符串/字节串适配
            if (isinstance(value, str) and
                    isinstance(getattr(req_obj, field), bytes)):
                value = value.encode('gbk')
            setattr(req_obj, field, value)
        else:
            print(f"警告：结构体无字段 {field}")


def print_ctp_object(obj, obj_name="Object"):
    """打印CTP结构体（来自td_demo的print_object）"""
    if not obj:
        print(f"{obj_name}: None")
        return
    attrs = []
    for attr in dir(obj):
        if not attr.startswith("_") and not callable(getattr(obj, attr)):
            val = getattr(obj, attr)
            if isinstance(val, bytes):
                val = val.decode("gbk", "ignore")
            attrs.append(f"{attr}={val}")
    print(f"{obj_name}: {', '.join(attrs)}")
