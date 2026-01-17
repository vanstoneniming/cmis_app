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

### 方式3：使用宝塔面板（推荐，图形化操作）

适合不熟悉命令行操作的开发者，通过可视化界面轻松部署和管理应用。

#### 前置要求

- 已安装宝塔面板（Linux版本）
- 服务器已安装 Python 3.8+（可在宝塔面板中安装）
- 已安装 Nginx（宝塔面板会自动安装）

#### 步骤1：上传项目文件

1. **通过宝塔文件管理器上传**
   - 登录宝塔面板
   - 进入"文件"菜单
   - 导航到 `/www/wwwroot/` 目录（或您希望的部署目录）
   - 点击"上传"，将项目文件压缩为 `.zip` 或 `.tar.gz` 后上传
   - 上传后解压文件

2. **或通过 Git 克隆**
   ```bash
   cd /www/wwwroot/
   git clone https://github.com/vanstoneniming/cmis_app.git
   cd cmis_app
   ```

#### 步骤2：创建 Python 虚拟环境

1. **在宝塔终端中执行**（或在宝塔面板的"终端"功能中执行）
   ```bash
   cd /www/wwwroot/cmis_app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. **或使用宝塔的 Python 项目管理器**
   - 进入"软件商店" → 搜索"Python项目管理器" → 安装
   - 进入"Python项目管理器" → 点击"添加Python项目"
   - 配置如下：
     - **项目名称**: `cmis_app`
     - **项目路径**: `/www/wwwroot/cmis_app`
     - **Python版本**: 选择已安装的 Python 3.8+ 版本
     - **项目类型**: 选择"其他"
     - **启动文件**: `app.py`
     - **启动方式**: 选择"命令行"
     - **运行目录**: `/www/wwwroot/cmis_app`
     - **启动命令**: `/www/wwwroot/cmis_app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0`
   - 点击"提交"创建项目

#### 步骤3：使用进程守护管理器（推荐方式）

1. **安装进程守护管理器**
   - 进入"软件商店" → 搜索"进程守护管理器" → 安装

2. **添加守护进程**
   - 进入"进程守护管理器" → 点击"添加守护进程"
   - 配置如下：
     - **名称**: `cmis_app`
     - **启动用户**: `root` 或您的用户名
     - **运行目录**: `/www/wwwroot/cmis_app`
     - **启动命令**: `/www/wwwroot/cmis_app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0`
     - **进程数量**: `1`
   - 点击"确认"创建守护进程
   - 点击"启动"启动应用

3. **查看运行状态**
   - 在"进程守护管理器"中可以查看进程状态、日志、重启等操作

#### 步骤4：配置 Nginx 反向代理

1. **添加站点**
   - 进入"网站"菜单 → 点击"添加站点"
   - **域名**: 输入您的域名（如 `cmis.yourdomain.com`）或使用IP地址
   - **根目录**: 可以保持默认或指向项目目录
   - **PHP版本**: 选择"纯静态"
   - 点击"提交"

2. **配置反向代理**
   - 在"网站"列表中找到刚创建的站点，点击"设置"
   - 进入"反向代理"标签页
   - 点击"添加反向代理"
   - 配置如下：
     - **代理名称**: `streamlit`
     - **目标URL**: `http://127.0.0.1:8501`
     - **发送域名**: 保持默认或填写 `$host`
     - **缓存**: 不开启
   - 点击"提交"

3. **修改 Nginx 配置（重要）**
   - 在反向代理设置页面，点击"配置文件"
   - 找到 `location /` 部分，修改为以下内容：
   ```nginx
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
       proxy_buffering off;
   }
   ```
   - 点击"保存"

#### 步骤5：配置防火墙端口

1. **开放端口（如果使用IP访问）**
   - 进入"安全"菜单
   - 在"系统防火墙"中添加规则：
     - **端口**: `8501`
     - **协议**: `TCP`
     - **策略**: `放行`
   - 点击"添加规则"

2. **或仅使用 Nginx 反向代理（推荐）**
   - 不对外开放 8501 端口，只通过 Nginx 的 80/443 端口访问
   - 在宝塔面板中确保 80 和 443 端口已开放

#### 步骤6：配置 SSL 证书（可选，推荐生产环境）

1. **使用宝塔 SSL**
   - 在网站设置中，进入"SSL"标签页
   - 选择"Let's Encrypt"免费证书
   - 输入邮箱，勾选域名
   - 点击"申请"
   - 申请成功后，开启"强制HTTPS"

2. **或使用已有证书**
   - 在"SSL"标签页选择"其他证书"
   - 粘贴证书内容

#### 步骤7：测试访问

1. **通过域名访问**
   - 如果配置了域名和SSL：`https://cmis.yourdomain.com`
   - 如果只有域名：`http://cmis.yourdomain.com`
   - 如果使用IP：`http://your-server-ip`

2. **查看日志**
   - 应用日志：在"进程守护管理器"中点击"日志"查看
   - Nginx日志：在"网站"设置中查看"日志"
   - Streamlit日志：在项目目录下查看，或在进程守护管理器日志中查看

#### 宝塔面板部署注意事项

1. **目录权限**
   - 确保 `data/` 目录有写权限
   ```bash
   chmod 755 /www/wwwroot/cmis_app/data
   ```

2. **进程守护**
   - 建议使用"进程守护管理器"而不是"Python项目管理器"，因为更稳定且易管理

3. **端口占用**
   - 如果 8501 端口被占用，可以在启动命令中修改端口号
   - 记得同步修改 Nginx 反向代理的目标URL

4. **内存优化**
   - 如果服务器内存较小，可以考虑限制进程内存使用
   - 在进程守护管理器中可以设置内存限制

5. **自动重启**
   - 进程守护管理器默认会监控进程状态，异常退出时自动重启

6. **更新代码**
   ```bash
   cd /www/wwwroot/cmis_app
   git pull  # 如果使用Git部署
   # 或在进程守护管理器中点击"重启"
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
