# 使用官方 conda 镜像作为基础镜像
FROM continuumio/miniconda3:latest

# 设置工作目录
WORKDIR /app

# 创建非 root 用户
RUN groupadd -r appuser && \
    useradd -r -g appuser -s /bin/bash appuser && \
    mkdir -p /app/config /app/logs && \
    chown -R appuser:appuser /app

# 复制项目文件
COPY --chown=appuser:appuser . /app/

# 创建 conda 环境
RUN conda create -n domain-sentinel python=3.12 -y && \
    echo "conda activate domain-sentinel" >> ~/.bashrc

# 设置 Shell
SHELL ["/bin/bash", "--login", "-c"]

# 安装依赖
RUN conda activate domain-sentinel && \
    pip install -r requirements.txt

# 设置卷
VOLUME ["/app/config", "/app/logs"]

# 切换到非 root 用户
USER appuser

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ps aux | grep python | grep app.py || exit 1

# 设置入口点
ENTRYPOINT ["conda", "run", "-n", "domain-sentinel", "python", "app.py"]