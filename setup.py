from setuptools import setup, find_packages
import os

# 读取requirements.txt文件


def read_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'),
              'r') as f:
        return [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]


setup(
    name="mytrade",
    version="0.1.0",
    author="",
    author_email="",
    description="CTP交易系统",
    long_description="CTP交易系统，支持行情接收和交易操作",
    long_description_content_type="text/plain",
    url="",
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'mytrade=main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
