# 使用轻量级的 Python 3.9 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖（如 git，用于获取版本号）
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（如果是 Web 服务需要，本项目主要是脚本运行）
# EXPOSE 8080

# 运行监控脚本
# 注意：Docker 部署通常需要循环运行模式，不带 --once 参数
CMD ["python", "DarkWeb-Forums-Tracker.py"]
