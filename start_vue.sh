#!/bin/bash

# CMIS 数据合并台（Vue 3 + TypeScript）启动脚本
set -e
cd "$(dirname "$0")"

if [ ! -d "node_modules" ]; then
  echo "正在安装前端依赖..."
  npm install
fi

echo "正在启动 Vue 开发服务器..."
npm run dev:host
