# signal_handler.py
import signal
import threading
import time

# 全局退出标志（线程安全）
EXIT_FLAG = threading.Event()

def signal_handler(signum, frame):
    """信号处理函数：捕获Ctrl+C/SIGTERM"""
    print(f"\nReceived signal {signum} (SIGINT/SIGTERM), exiting gracefully...")
    EXIT_FLAG.set()

def register_signals():
    """注册信号监听"""
    signal.signal(signal.SIGINT, signal_handler)   # 捕获Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 捕获kill命令

def run_in_background(func, *args, daemon=True):
    """
    在后台线程运行指定函数，直到EXIT_FLAG触发
    :param func: 要运行的函数（如MD API事件循环）
    :param args: 函数参数
    :param daemon: 是否设为守护线程
    :return: 启动的线程对象
    """
    def wrapper():
        # 执行目标函数
        func(*args)
        # 函数执行完成后触发退出
        EXIT_FLAG.set()

    thread = threading.Thread(target=wrapper, args=(), daemon=daemon)
    thread.start()
    return thread

def wait_for_exit():
    """主线程等待退出标志触发"""
    while not EXIT_FLAG.is_set():
        time.sleep(0.5)

def stop_background_thread(thread, timeout=5):
    """等待后台线程退出"""
    if thread and thread.is_alive():
        thread.join(timeout=timeout)
        if thread.is_alive():
            print(f"Warning: Background thread did not exit within {timeout}s")