# signal_handler.py
import signal
import threading
import time
import sys

# 全局退出标志（线程安全）
EXIT_FLAG = threading.Event()
# 用于跟踪所有后台线程
background_threads = []

def signal_handler(signum, frame):
    """信号处理函数：捕获Ctrl+C/SIGTERM，确保只处理一次"""
    if not EXIT_FLAG.is_set():
        print(f"\nReceived signal {signum} (SIGINT/SIGTERM), exiting gracefully...")
        EXIT_FLAG.set()
        # 立即终止主程序，避免重复处理信号
        sys.exit(0)

def register_signals():
    """注册信号监听"""
    signal.signal(signal.SIGINT, signal_handler)   # 捕获Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 捕获kill命令
    # Windows不支持signal.siginterrupt，移除该调用

def run_in_background(func, *args, daemon=True):
    """
    在后台线程运行指定函数，直到EXIT_FLAG触发
    :param func: 要运行的函数（如MD API事件循环）
    :param args: 函数参数
    :param daemon: 是否设为守护线程
    :return: 启动的线程对象
    """
    def wrapper():
        try:
            # 执行目标函数
            func(*args)
        finally:
            # 函数执行完成后触发退出
            EXIT_FLAG.set()

    thread = threading.Thread(target=wrapper, args=(), daemon=daemon)
    thread.start()
    # 跟踪后台线程
    background_threads.append(thread)
    return thread

def wait_for_exit():
    """主线程等待退出标志触发"""
    try:
        while not EXIT_FLAG.is_set():
            # 使用更短的轮询间隔，提高响应速度
            time.sleep(0.01)
    except KeyboardInterrupt:
        # 确保Ctrl+C能够立即中断等待
        if not EXIT_FLAG.is_set():
            EXIT_FLAG.set()


def stop_background_thread(thread, timeout=2):
    """等待后台线程退出"""
    if thread and thread.is_alive():
        thread.join(timeout=timeout)
        if thread.is_alive():
            print(f"Warning: Background thread did not exit within {timeout}s")


def stop_all_background_threads(timeout=2):
    """停止所有后台线程"""
    for thread in background_threads:
        if thread.is_alive():
            thread.join(timeout=timeout)
            if thread.is_alive():
                print(f"Warning: Background thread did not exit within {timeout}s")
    # 清空线程列表
    background_threads.clear()