# KHunter Docker 部署说明

A股量化选股系统（Flask + Flask-SocketIO）的容器化部署方案。

## 1. 组成

| 文件 | 作用 |
|------|------|
| `Dockerfile` | 镜像定义，基础镜像 `python:3.14-slim`（与项目 `.venv` 的 Python 3.14 对齐） |
| `docker-compose.yml` | 编排：端口映射、数据卷、健康检查、自动重启 |
| `docker/entrypoint.sh` | 容器入口：确保运行期目录存在后启动 `web_server.py` |
| `.dockerignore` | 构建上下文排除项，保持镜像精简 |

## 2. 快速开始

```bash
cd /mnt/e/code/github/KHunter

# 构建 + 启动（后台）
docker compose up -d --build

# 查看状态 / 健康
docker compose ps
docker inspect --format '{{.State.Health.Status}}' khunter

# 跟踪日志
docker compose logs -f khunter

# 停止 / 移除
docker compose down            # 保留数据卷
docker compose down -v         # 仅删编排网络（数据在宿主机目录，不受影响）
```

访问：<http://localhost:5001>

## 3. 端口与数据卷

- 端口：容器内 `5001` → 宿主 `5001`（`web_server.py` 的 `__main__` 固定监听 `0.0.0.0:5001`）
- 数据卷（全部绑定到租户仓库目录，保证持久化）：

| 宿主 | 容器 | 内容 |
|------|------|------|
| `./config` | `/app/config` | 钉钉/数据源密钥、策略参数（**可写**：策略参数改动需落盘） |
| `./data` | `/app/data` | SQLite 库、行情缓存、回测队列、持仓/信号 |
| `./logs` | `/app/logs` | 运行日志 |
| `./reports` | `/app/reports` | 生成的报告 |

> `data/DataSql.sql`、`data/InitData.sql` 是建库脚本（必需）。它们保留在仓库中被挂载进容器，故首次启动即可自动建表。

## 4. 镜像内已处理的适配点

- **时区**：`TZ=Asia/Shanghai` + `tzdata`，保证交易时段/AKShare 时间戳正确。
- **matplotlib 后端**：`MPLBACKEND=Agg`（无显示器环境必须）。
- **中文字体**：安装 `fonts-wqy-microhei` 并在构建期预建字体缓存（`fm.findfont('WenQuanYi Micro Hei')` 已在构建日志中命中 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc`）。
- **依赖补全**：`requirements.txt` 原缺 `openpyxl`、`pytz`、`tushare`，代码中确有引用（`tushare` 为顶层强依赖，缺失会导致 `/api/risk/status` 等 500），已补齐。
- **pip 源**：`Dockerfile`/`compose` 暴露 `PIP_INDEX_URL` 构建参数，国内可改为 `https://pypi.tuna.tsinghua.edu.cn/simple`。

## 5. 代码变更后如何更新

```bash
docker compose up -d --build     # 重新构建并以新镜像重建容器
```

依赖未变时，pip 层走缓存，仅重跑 `COPY . .`，秒级完成。

## 6. 已知事项

- **开发服务器告警**：`web_server.py` 用 Flask 内置服务器（werkzeug）启动，日志会提示 "development server"。单机内网使用无碍；若要上生产，建议改为 `gunicorn --worker-class eventlet -w 1 web_server:app`（SocketIO `async_mode='threading'`，需对应 worker）。
- **图表中文**：`utils/kline_chart.py` 把字体列表写成 `['DejaVu Sans', 'SimHei', ...]`，`DejaVu Sans` 排首位且无中文字形，容器内可能出现方块。`kline_chart_fast.py` 未设字体走默认，正常。若要彻底解决，把 `WenQuanYi Micro Hei` 调到列表首位（或设置 `matplotlib.rcParams` 全局）。
- **容器不继承宿主代理**：`akshare`/`tushare` 拉取的是国内数据源，无需代理；若宿主仅在代理下可访问某些源，需自行给容器配置 `HTTPS_PROXY` 环境变量。
- **敏感信息**：`config/tushare_config.json`（真实 tushare token）与 `config/config.yaml` 已被提交进 Git，属于泄漏项，建议改用环境变量或未提交的配置文件，并将配置目录移出版本控制。

## 7. 验证记录（2026-10-09）

- 镜像构建成功，`CJK font` 命中 WenQuanYi Micro Hei。
- 容器健康状态 `healthy`，`GET /` 返回 `200`，页面标题 `形态猎手-KHunter`。
- 28 个只读 GET 接口轮询：全部 `200`（`/api/khunter/check-cache`、`/api/khunter/latest_kline_date` 返回 `400` 属正常参数校验，非故障）。
- 持久化确认：容器在宿主 `data/stock_selection.db`（442KB）建库、写入 `logs/app.2026-10-09.log`。
