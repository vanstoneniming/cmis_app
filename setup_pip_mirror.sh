#!/bin/bash

# 配置pip使用国内镜像源的脚本

echo "正在配置pip使用清华大学镜像源..."

# 创建pip配置目录
mkdir -p ~/.pip 2>/dev/null || mkdir -p ~/.config/pip 2>/dev/null

# 检测pip配置目录
if [ -d ~/.pip ]; then
    PIP_DIR=~/.pip
    PIP_FILE="$PIP_DIR/pip.conf"
elif [ -d ~/.config/pip ]; then
    PIP_DIR=~/.config/pip
    PIP_FILE="$PIP_DIR/pip.conf"
else
    PIP_DIR=~/.pip
    mkdir -p "$PIP_DIR"
    PIP_FILE="$PIP_DIR/pip.conf"
fi

# 写入配置
cat > "$PIP_FILE" << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

echo "✅ 配置已保存到: $PIP_FILE"
echo ""
echo "配置内容："
cat "$PIP_FILE"
echo ""
echo "现在可以直接使用 'pip install' 命令，会自动使用清华大学镜像源！"

