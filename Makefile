# Makefile for mytrade project

.PHONY: install clean

# 安装项目
install:
	@echo "Installing mytrade..."
	pip install -e .
	@echo "Installation completed successfully!"

# 清理项目
clean:
	@echo "Cleaning mytrade..."
	# 使用Python脚本进行跨平台清理
	python -c "
import os
import shutil
import glob

# 定义要删除的目录和文件
paths_to_delete = [
    'build',
    'dist',
    '*.egg-info',
    './mytrade/conf',
    './mytrade/logs',
    './mytrade/db',
    './mydb',
    './mytrade/streams'
]

# 删除目录和文件
for path in paths_to_delete:
    if '*' in path:
        # 处理通配符
        for match in glob.glob(path):
            try:
                if os.path.isdir(match):
                    shutil.rmtree(match)
                    print(f'Deleted directory: {match}')
                elif os.path.isfile(match):
                    os.remove(match)
                    print(f'Deleted file: {match}')
            except Exception as e:
                print(f'Error deleting {match}: {e}')
    else:
        # 处理普通路径
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f'Deleted directory: {path}')
            elif os.path.isfile(path):
                os.remove(path)
                print(f'Deleted file: {path}')
        except Exception as e:
            print(f'Error deleting {path}: {e}')

# 删除__pycache__目录
for root, dirs, files in os.walk('.'):
    for dir_name in dirs:
        if dir_name == '__pycache__':
            pycache_path = os.path.join(root, dir_name)
            try:
                shutil.rmtree(pycache_path)
                print(f'Deleted __pycache__: {pycache_path}')
            except Exception as e:
                print(f'Error deleting {pycache_path}: {e}')
"
	@echo "Cleanup completed successfully!"
