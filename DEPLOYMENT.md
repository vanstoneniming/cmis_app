# 🚀 CMIS成绩处理辅助工具 - 部署指南

本指南提供了多种部署方式，您可以根据需求选择合适的部署方案。

## 📋 目录

1. [本地部署](#本地部署)
2. [Streamlit Cloud 部署（推荐）](#streamlit-cloud-部署推荐)
3. [Docker 部署](#docker-部署)
4. [服务器部署（生产环境）](#服务器部署生产环境)
5. [常见问题](#常见问题)

---

## 🖥️ 本地部署

适用于开发和测试环境。

### 前置要求

- Python 3.8 或更高版本
- pip 包管理器

### 步骤

1. **克隆或下载项目**
   ```bash
   cd /path/to/your/project
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   ```

3. **激活虚拟环境**
   
   macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   
   Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

5. **运行应用**
   ```bash
   # 方式1：使用启动脚本
   ./start.sh  # macOS/Linux
   start.bat   # Windows
   
   # 方式2：直接运行
   streamlit run app.py
   ```

6. **访问应用**
   浏览器会自动打开，或手动访问 `http://localhost:8501`

---

## ☁️ Streamlit Cloud 部署（推荐）

最简单快速的云端部署方式，免费且无需服务器。

### 前置要求

- GitHub 账号
- GitHub 仓库（将项目代码推送到 GitHub）

### 步骤

1. **准备 GitHub 仓库**
   ```bash
   # 在项目根目录初始化 git（如果还没有）
   git init
   git add .
   git commit -m "Initial commit"
   
   # 创建 GitHub 仓库，然后推送
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

2. **配置 Streamlit Cloud**
   - 访问 [Streamlit Cloud](https://streamlit.io/cloud)
   - 使用 GitHub 账号登录
   - 点击 "New app"
   - 选择您的 GitHub 仓库
   - 设置配置：
     - **Main file path**: `app.py`
     - **Python version**: 3.11（或您需要的版本）
   - 点击 "Deploy"

3. **访问应用**
   部署完成后，Streamlit Cloud 会提供一个公开的 URL，例如：
   `https://your-app-name.streamlit.app`

### 注意事项

- Streamlit Cloud 免费版适合个人和小型项目
- 数据会存储在应用的临时文件系统中（重启可能丢失）
- 如需持久化存储，可以考虑使用外部存储服务

---

## 🐳 Docker 部署

适合在任何支持 Docker 的环境部署（本地、云服务器等）。

### 前置要求

- Docker 已安装
- Docker Compose（可选，但推荐）

### 步骤

1. **创建 Dockerfile**

   在项目根目录创建 `Dockerfile`：
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # 安装系统依赖
   RUN apt-get update && apt-get install -y \
       build-essential \
       && rm -rf /var/lib/apt/lists/*

   # 复制依赖文件
   COPY requirements.txt .

   # 安装 Python 依赖
   RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

   # 复制应用代码
   COPY . .

   # 创建数据目录
   RUN mkdir -p /app/data

   # 暴露端口
   EXPOSE 8501

   # 健康检查
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

   # 启动应用
   ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **创建 .dockerignore**

   ```
   venv/
   __pycache__/
   *.pyc
   .git/
   .gitignore
   data/
   *.pkl
   *.db
   ```

3. **构建 Docker 镜像**
   ```bash
   docker build -t cmis-grade-tool .
   ```

4. **运行容器**
   ```bash
   docker run -d \
     -p 8501:8501 \
     -v $(pwd)/data:/app/data \
     --name cmis-app \
     cmis-grade-tool
   ```

5. **使用 Docker Compose（推荐）**

   创建 `docker-compose.yml`：
   ```yaml
   version: '3.8'

   services:
     app:
       build: .
       ports:
         - "8501:8501"
       volumes:
         - ./data:/app/data
       restart: unless-stopped
       environment:
         - STREAMLIT_SERVER_PORT=8501
         - STREAMLIT_SERVER_ADDRESS=0.0.0.0
   ```

   运行：
   ```bash
   docker-compose up -d
   ```

6. **访问应用**
   访问 `http://localhost:8501`

---

## 🖥️ 服务器部署（生产环境）

适合在生产服务器上长期运行。

### 前置要求

- Linux 服务器（Ubuntu/Debian 推荐）
- Python 3.8+
- Nginx（可选，用于反向代理）

### 方式1：使用 systemd（推荐）

1. **创建 systemd 服务文件**

   ```bash
   sudo nano /etc/systemd/system/cmis-app.service
   ```

   内容：
   ```ini
   [Unit]
   Description=CMIS Grade Processing Tool
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/your/app
   Environment="PATH=/path/to/your/app/venv/bin"
   ExecStart=/path/to/your/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. **启用并启动服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cmis-app
   sudo systemctl start cmis-app
   ```

3. **查看状态**
   ```bash
   sudo systemctl status cmis-app
   ```

### 方式2：使用 Supervisor

1. **安装 Supervisor**
   ```bash
   sudo apt-get install supervisor
   ```

2. **创建配置文件**
   ```bash
   sudo nano /etc/supervisor/conf.d/cmis-app.conf
   ```

   内容：
   ```ini
   [program:cmis-app]
   command=/path/to/your/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   directory=/path/to/your/app
   user=your-username
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/cmis-app.err.log
   stdout_logfile=/var/log/cmis-app.out.log
   ```

3. **启动服务**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start cmis-app
   ```

### 配置 Nginx 反向代理（可选）

1. **安装 Nginx**
   ```bash
   sudo apt-get install nginx
   ```

2. **创建 Nginx 配置**
   ```bash
   sudo nano /etc/nginx/sites-available/cmis-app
   ```

   内容：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

3. **启用配置**
   ```bash
   sudo ln -s /etc/nginx/sites-available/cmis-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **配置 HTTPS（可选，使用 Let's Encrypt）**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## ❓ 常见问题

### Q1: 如何修改端口？

在启动命令中指定端口：
```bash
streamlit run app.py --server.port=8080
```

或在 `.streamlit/config.toml` 中配置：
```toml
[server]
port = 8080
```

### Q2: 如何配置允许的外部访问？

```bash
streamlit run app.py --server.address=0.0.0.0
```

### Q3: 数据如何持久化？

- **本地部署**：数据保存在 `data/` 目录下的 `grades_data.pkl` 文件
- **Docker 部署**：使用 volume 挂载数据目录
- **服务器部署**：确保 `data/` 目录有写权限，定期备份

### Q4: 如何备份数据？

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf backup-20240116.tar.gz
```

### Q5: 如何更新应用？

1. 拉取最新代码
2. 更新依赖：`pip install -r requirements.txt --upgrade`
3. 重启服务（根据部署方式选择）
   - systemd: `sudo systemctl restart cmis-app`
   - supervisor: `sudo supervisorctl restart cmis-app`
   - Docker: `docker-compose restart`

### Q6: 性能优化建议

- 对于大量数据，考虑使用数据库替代 pickle 文件
- 配置适当的内存限制
- 使用反向代理缓存静态资源
- 考虑使用 Redis 缓存会话数据

---

## 📞 技术支持

如有部署问题，请查看：
- [Streamlit 官方文档](https://docs.streamlit.io/)
- [Docker 官方文档](https://docs.docker.com/)
- 项目 Issues

---

**祝部署顺利！** 🎉
