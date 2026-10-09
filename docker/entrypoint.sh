#!/usr/bin/env bash
# KHunter 容器入口：确保运行期目录存在后启动 Web 服务
set -euo pipefail

mkdir -p \
    data \
    data/akshare_cache \
    data/cache \
    data/backtest_batch \
    data/running \
    logs \
    reports

# 首个参数是额外传给 web_server.py 的（默认无参数）
exec python web_server.py "$@"
