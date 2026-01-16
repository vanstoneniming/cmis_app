@echo off
REM CMIS成绩处理辅助工具启动脚本（Windows）

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查依赖是否已安装
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo 正在安装依赖（使用清华大学镜像源）...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM 启动应用
echo 正在启动应用...
streamlit run app.py

pause

