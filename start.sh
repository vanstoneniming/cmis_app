#!/bin/bash

# CMIS成绩处理辅助工具启动脚本

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import streamlit" 2>/dev/null; then
    echo "正在安装依赖（使用清华大学镜像源）..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 启动应用
echo "正在启动应用..."
export STREAMLIT_SERVER_FOLDER_PATH=/tmp/.streamlit
mkdir -p /tmp/.streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --browser.gatherUsageStats=false --server.enableCORS=false --server.enableXsrfProtection=false --server.enableWebsocketCompression=false

