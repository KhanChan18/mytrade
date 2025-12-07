# ctp_utils.py
def set_req_fields(req, field_dict):
    """
    通用Req对象字段赋值工具
    :param req: CTP的Req对象
    :param field_dict: 字段名-值字典（空值/None会被忽略）
    """
    if not req or not isinstance(field_dict, dict):
        return
    
    for field, value in field_dict.items():
        # 忽略空值
        if value is None or value == "":
            continue
        
        # 检查字段是否存在
        if not hasattr(req, field):
            continue
        
        # 类型转换（适配CTP字段类型）
        try:
            field_type = type(getattr(req, field))
            if field_type == int and isinstance(value, str):
                value = int(value)
            elif field_type == float and isinstance(value, str):
                value = float(value)
            
            # 赋值
            setattr(req, field, value)
        except Exception as e:
            print(f"字段赋值失败 {field}={value}: {e}")