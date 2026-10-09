# KHunter Docker 部署说明

A股量化选股系统（Flask + Flask-SocketIO）的容器化部署方案。

## 1. 组成

| 文件 | 作用 |
|------|------|
| `Dockerfile` | 镜像定义，基础镜像 `python:3.14-slim`（与项目 `.venv` 的 Python 3.14 对齐） |
| `docker-compose.yml` | 编排：端口映射、数据卷、健康检查、自动重启 |
| `docker/entrypoint.sh` | 容器入口：确保运行期目录存在后启动 `web_server.py` |
| `.dockerignore` | 构建上下文排除项，保持镜像精简且不打包密钥 |

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

# 停止
docker compose down
```

访问：<http://localhost:5001>

## 3. 端口与数据卷

- 端口：容器内 `5001` → 宿主 `5001`（`web_server.py` 的 `__main__` 固定监听 `0.0.0.0:5001`）
- 数据卷（全部绑定到仓库目录，保证持久化）：

| 宿主 | 容器 | 内容 |
|------|------|------|
| `./config` | `/app/config` | 钉钉/数据源密钥、策略参数（**可写**：策略参数改动需落盘） |
| `./data` | `/app/data` | SQLite 库、行情缓存、回测队列、持仓/信号 |
| `./logs` | `/app/logs` | 运行日志 |
| `./reports` | `/app/reports` | 生成的报告 |

> `data/DataSql.sql`、`data/InitData.sql` 是建库脚本（必需），保留在仓库中随 `./data` 挂载进容器，首次启动自动建表。
> 密钥文件 `config/tushare_config.json` 不进镜像，运行期由 `./config` 挂载提供（见第 7 节）。

## 4. 镜像内已处理的适配点

- **时区**：`TZ=Asia/Shanghai` + `tzdata`。
- **matplotlib 后端**：`MPLBACKEND=Agg`（无显示器环境必须）。
- **中文字体**：安装 `fonts-wqy-microhei`，构建期预建字体缓存；K线图模块字体列表已调整为中文优先（见第 7 节）。
- **依赖补全**：`requirements.txt` 补齐 `openpyxl`、`pytz`、`tushare`。
- **pip 源**：`Dockerfile`/`compose` 暴露 `PIP_INDEX_URL` 构建参数，国内可改为 `https://pypi.tuna.tsinghua.edu.cn/simple`。

## 5. 代码变更后如何更新

```bash
docker compose up -d --build     # 重新构建并以新镜像重建容器
```

依赖未变时，pip 层走缓存，仅重跑 `COPY . .`，秒级完成。

## 6. 生产化建议（未改动）

`web_server.py` 用 Flask 内置服务器（werkzeug）启动，日志会提示 "development server"。
内网单机使用无碍。若要对外，建议改用 `gunicorn --worker-class gthread --workers 1 web_server:app`
（SocketIO `async_mode='threading'` 且应用持有进程内状态与后台线程，必须单 worker）。
**此项涉及运行时可观测性与长连接行为，属架构调整而非缺陷，未擅自改动。**

另：容器不继承宿主代理。`akshare`/`tushare` 拉取的是国内数据源，无需代理；若某些源仅在代理下可达，
需自行给容器注入 `HTTPS_PROXY`。

## 7. 本轮修复记录（2026-10-09）

### (1) tushare token 读不到（静默降级）— 已修
`config/tushare_config.json` 的键为 `tushare_token`，但全部读取端（`event_scorer`/`fundamental_scorer`/
`moneyflow_scorer`/`sector_scorer`/`stock_data_fetcher`/`backtest_engine`/`exdividend_utils`/
`fund_flow_fetcher`/`data_collectors`）读取的是 `token` 或 `api_key`，导致 token 永远为空、
基本面/资金流/板块/事件评分静默降级。已把配置键统一为 `token`。
验证：容器内 `MoneyflowScorer()._load_tushare_token()` 返回长度 56 的 token（修复前为空）。

### (2) 真实密钥进入版本控制 — 已修
`config/tushare_config.json` 含真实 tushare token 且被 git 跟踪。已 `git rm --cached` 并加入
`.gitignore`，同时新增 `config/tushare_config.json.template`；`.dockerignore` 排除该文件，
镜像不再打包密钥（无挂载 `docker run` 验证：`/app/config/tushare_config.json` 不存在）。
> ⚠️ 历史提交中仍残留该 token，**必须在 tushare 后台轮换**才能彻底止损（此动作需你本人操作）。

`config/config.yaml` 同样按作者原意（文件内已注明"勿提交"）移出版本控制，`config.yaml.template` 已补全 `filters`/`trading` 段。

### (3) SQLite 边车文件被 git 跟踪 — 已修
`data/stock_selection.db-shm` / `-wal` 曾被跟踪，容器一写库就把仓库标脏。已 `git rm --cached`
并加入 `.gitignore`（`*.db-shm`、`*.db-wal`）。

### (4) K线图中文显示为方块 — 已修
`utils/kline_chart.py` 字体列表把 `DejaVu Sans`（无中文字形）排在首位；`kline_chart_fast.py` 未设字体。
两者均已改为 `['WenQuanYi Micro Hei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']`
（Windows 命中 SimHei/雅黑，Linux 容器命中文泉驿）。
验证：容器内渲染中文标题/轴标签，把 `UserWarning` 提升为异常后仍无 "Glyph missing"，成功出图。

## 8. 验证记录（2026-10-09）

- 镜像构建成功，`CJK font` 命中 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc`。
- 容器健康状态 `healthy`，`GET /` 返回 `200`，页面标题 `形态猎手-KHunter`。
- 28 个只读 GET 接口轮询：全部 `200`（`/api/khunter/check-cache`、`/api/khunter/latest_kline_date` 返回
  `400` 属正常参数校验，非故障）；`/api/risk/status` 修复后由 `500` → `200`。
- 持久化确认：容器在宿主 `data/stock_selection.db` 建库、写入 `logs/app.<日期>.log`。
