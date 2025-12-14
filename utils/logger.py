from datetime import datetime
import inspect
import os

from config import LOG_FILE
from utils.log_templates import LOG_TEMPLATES


class Logger:
    # 业务对象打印字段模板（从utils.log_templates导入）
    PRINT_TEMPLATES = LOG_TEMPLATES

    def __init__(self, log_file=None, log_level="INFO"):
        """
        初始化日志器
        :param log_file: 日志文件路径（None则仅控制台输出）
        :param log_level: 日志等级，可选 DEBUG/INFO/ERROR，默认 INFO
        """
        self._base_log_file = log_file
        self._current_log_file = log_file
        self._current_log_date = None

        # 日志等级校验，非法值默认INFO
        level_upper = log_level.upper()
        if level_upper in ["DEBUG", "INFO", "ERROR"]:
            self._log_level = level_upper
        else:
            self._log_level = "INFO"

        # 初始化当前日志文件和日期
        if log_file:
            self._update_log_file()

    def _update_log_file(self):
        """
        根据当前日期更新日志文件路径
        如果日期变化，创建新的日志文件
        """
        if not self._base_log_file:
            return

        # 获取当前日期（YYYY-MM-DD）
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 如果日期变化或当前日志文件未设置，更新日志文件路径
        if current_date != self._current_log_date:
            # 构建新的日志文件路径（在文件名中添加日期）
            dir_path, file_name = os.path.split(self._base_log_file)
            name, ext = os.path.splitext(file_name)
            new_file_name = f"{name}_{current_date}{ext}"
            self._current_log_file = os.path.join(dir_path, new_file_name)
            self._current_log_date = current_date

    def set_log_file(self, log_file):
        """
        动态设置日志文件路径
        :param log_file: 新的日志文件路径（None则仅控制台输出）
        """
        self._base_log_file = log_file
        self._current_log_file = log_file
        self._current_log_date = None
        if log_file:
            self._update_log_file()

    def set_log_level(self, log_level):
        """
        动态设置日志等级
        :param log_level: 新的日志等级，可选 DEBUG/INFO/ERROR
        """
        level_upper = log_level.upper()
        if level_upper in ["DEBUG", "INFO", "ERROR"]:
            self._log_level = level_upper
        else:
            self._log_level = "INFO"

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
            if "/" in file_name:
                short_file = file_name.split("/")[-1]
            else:
                short_file = file_name.split("\\")[-1]

            line_no = frame.lineno  # 行号
            func_name = frame.function  # 调用函数名
            return f"{short_file}: {line_no}({func_name})"
        except Exception:
            # 降级处理：兼容栈层级异常的情况
            frame = inspect.stack()[2]
            file_name = frame.filename

            if "/" in file_name:
                short_file = file_name.split("/")[-1]
            else:
                short_file = file_name.split("\\")[-1]

            line_no = frame.lineno
            func_name = frame.function
            return f"{short_file}: {line_no}({func_name})"

    def print_log(self, level, prefix, content):
        """
        统一日志打印（DEBUG级包含行号，INFO/ERROR简化）
        """
        # 日志等级标准化
        level_upper = level.upper()
        if level_upper in ["DEBUG", "INFO", "ERROR"]:
            level = level_upper
        else:
            level = "INFO"

        # 日志级别过滤：低于设置等级的日志不输出
        level_priority = {"DEBUG": 0, "INFO": 1, "ERROR": 2}
        if level_priority[level] < level_priority[self._log_level]:
            return

        # 构建日志字符串（按级别区分格式）
        timestamp = self.get_timestamp()
        if level == "DEBUG":
            caller_info = self.get_caller_info()
            log_str = (f"[{timestamp}] [{level}] [{caller_info}] "
                       f"{prefix}: {content}")
        else:
            # INFO/ERROR简化格式
            log_str = f"[{timestamp}] [{level}] {prefix}: {content}"

        # 控制台输出
        print(log_str)

        # 写入文件（使用按日更新的日志文件）
        self._update_log_file()  # 每次写入前检查日期是否变化
        if self._current_log_file:
            try:
                with open(self._current_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_str + "\n")
            except Exception as e:
                print(f"日志写入失败: {e}")

    def print_error(self, func_name, pRspInfo):
        """
        通用错误打印（带行号）
        """
        if (pRspInfo and hasattr(pRspInfo, 'ErrorID') and
                pRspInfo.ErrorID != 0):
            self.print_log("ERROR", func_name, f"失败: {pRspInfo.ErrorMsg}")
            return True
        return False

    def print_object(self, prefix, obj, template_name):
        """
        通用对象打印（带行号）
        """
        if not obj:
            return

        field_list = self.PRINT_TEMPLATES.get(template_name, [])
        field_pairs = [f"{k}={getattr(obj, k, 'N/A')}" for k in field_list]
        fields_str = " ".join(field_pairs)
        self.print_log("INFO", prefix, fields_str)

    # 快捷方法（保持不变）
    def debug(self, prefix, content):
        self.print_log("DEBUG", prefix, content)

    def info(self, prefix, content):
        self.print_log("INFO", prefix, content)

    def error(self, prefix, content):
        self.print_log("ERROR", prefix, content)


# 创建全局日志实例
main_logger = Logger(log_file=LOG_FILE, log_level="INFO")
