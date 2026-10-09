# syntax=docker/dockerfile:1
# ============================================================
# KHunter - A股量化选股系统 容器镜像
# 基础镜像与项目 .venv 对齐（Python 3.14）
# ============================================================
FROM python:3.14-slim

# 运行期环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    MPLBACKEND=Agg

# 系统依赖：
#   tzdata            -> A股交易时段/AKShare 时间戳依赖正确的时区
#   fonts-wqy-microhei-> K线图中文标签（代码 font.sans-serif 列表中已含该字体名）
# 构建期可切换 pip 源（国内可传 https://pypi.tuna.tsinghua.edu.cn/simple）
ARG PIP_INDEX_URL=https://pypi.org/simple

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata fonts-wqy-microhei \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖，利用 Docker 层缓存：只有 requirements.txt 变化才重装
COPY requirements.txt ./
RUN pip install --index-url "${PIP_INDEX_URL}" -r requirements.txt

# 预建 matplotlib 字体缓存，确保容器内首次绘图即可命中中文字体
RUN python -c "import matplotlib.font_manager as fm; print('CJK font ->', fm.findfont('WenQuanYi Micro Hei'))"

# 拷贝项目源码（排除项见 .dockerignore）
COPY . .

# 运行期目录（挂载点占位）
RUN mkdir -p data logs reports data/akshare_cache data/cache data/backtest_batch data/running \
    && chmod +x docker/entrypoint.sh

EXPOSE 5001

# 容器健康检查：TCP 探测 Web 端口
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 5001), 5)" || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
