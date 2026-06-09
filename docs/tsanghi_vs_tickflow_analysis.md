# Tsanghi 数据源替换为 TickFlow 的可行性分析

> 分析日期：2026-05-25  
> TickFlow 文档参考：https://docs.tickflow.org/zh-Hans

---

## 1. 当前 Tsanghi 数据源使用概况

Grider 项目以 Tsanghi（沧海数据）为唯一外部金融数据源，支撑 ETF 网格策略分析和回测的全部数据需求。共计 9 个 API 端点，通过 `TsanghiProvider` 统一调用。

### 1.1 端点清单与业务用途

| 端点 | 方法 | 业务用途 | 缓存策略 |
|---|---|---|---|
| `exchange` | 获取交易所列表 | ETF 分析入口 | 1 年 |
| `calendar` | 交易日历 | 回测日期计算 | 1 天 |
| `search` | 代码模糊搜索 | 用户输入 ticker 查找标的 | 1 天 |
| `stock_realtime` | 股票实时行情 | 获取最新价格 | 3 小时 |
| `stock_daily` | 股票日 K 线 | 策略分析历史数据 | 1 年 |
| `stock_5min` | 股票 5 分钟 K 线 | 回测精细模拟 | 1 年 |
| `etf_realtime` | ETF 实时行情 | 获取 ETF 最新价格 | 3 小时 |
| `etf_daily` | ETF 日 K 线 | ETF 策略分析 | 1 年 |
| `etf_5min` | ETF 5 分钟 K 线 | ETF 回测 | 1 年 |

### 1.2 调用链

```
前端 → Flask Route → Service → DataService → TsanghiProvider → BaseProvider(缓存/认证/HTTP) → Tsanghi API
```

### 1.3 关键业务场景依赖

- **策略分析** (`POST /api/grid/analyze`)：`search_by_ticker` → `get_latest_price` → `get_daily_data`
- **策略回测** (`POST /api/grid/backtest`)：`get_trading_calendar` → `get_5min_kline`

---

## 2. TickFlow API 能力映射

### 2.1 端点对应关系

| Tsanghi 端点 | TickFlow 对应 | 匹配度 | 备注 |
|---|---|---|---|
| `exchange` | `tf.exchanges` / `tf.universes.list()` | ✅ 可替代 | TickFlow 通过交易所和标的池接口提供更丰富的元数据 |
| `calendar` | **未找到** | ❌ 缺失 | 无交易日历 API，这是回测模块的核心依赖 |
| `search` | `tf.instruments.batch()` | ⚠️ 部分可替 | 仅支持精确代码查询，不支持模糊搜索和分页 |
| `stock_realtime` | `tf.quotes.get(symbols=[...])` | ✅ 可替代 | 支持批量查询，返回字段更丰富 |
| `stock_daily` | `tf.klines.get(period="1d")` | ✅ 可替代 | 支持 count/时间范围/复权，功能更强 |
| `stock_5min` | `tf.klines.get(period="5m")` | ✅ 可替代 | 需付费订阅，仅 A 股支持分钟线 |
| `etf_realtime` | `tf.quotes.get(symbols=[...])` | ✅ 可替代 | 统一接口，不区分股票/ETF |
| `etf_daily` | `tf.klines.get(period="1d")` | ✅ 可替代 | 同上 |
| `etf_5min` | `tf.klines.get(period="5m")` | ✅ 可替代 | 同上 |

**总体：9 个端点中，7 个可直接替代，1 个部分可替代，1 个缺失。**

---

## 3. 关键差异分析

### 3.1 ✅ 交易日历 API（已解决）

TickFlow 文档中未提供交易日历 API 端点，但可通过离线库 **`exchange_calendars`**（Apache-2.0, v4.13.2, 609⭐, 100 贡献者）完美替代：

```python
import exchange_calendars as xcals

xshg = xcals.get_calendar("XSHG")   # 上交所 → A 股（沪深共用）
xshg.is_session("2025-01-01")        # False（元旦休市）
xshg.sessions_in_range("2025-01-01", "2025-01-10")  # 交易日列表
xhkg = xcals.get_calendar("XHKG")   # 港股（可选扩展）
xnys = xcals.get_calendar("XNYS")   # 美股（可选扩展）
```

**为什么选它而不是其他方案：**

| 方案 | 市场覆盖 | 维护成本 | 适用性 |
|---|---|---|---|
| **`exchange_calendars`** | A股 + 港股 + 美股（60+交易所） | `pip install` 即用，偶尔升级 | ⭐ 一库覆盖全部 |
| `cn-stock-holidays` | 沪深 + 港股 | 需 cron 每日 sync | A 股专用好，跨市场需另加库 |
| `hhxg.top` 免费 API | A 股 | 依赖外部服务可用性 | 轻量但有网络风险 |
| 保留 Tsanghi calendar | A 股 + 港股 | 继续付费 + 维护 Tsanghi | 违背替换初衷 |

**关于临时休市（台风等）的补充说明：**
- A 股几乎无天气临时休市（30 年仅 2020 年新冠延期开市 1 次），后续若有重大事件可通过 `pip install --upgrade exchange_calendars` 更新
- 港交所自 **2024 年 9 月 23 日**起实施恶劣天气不停市制度，未来港股不再产生台风休市
- 如需最高确定性，可在配置中预留 `adhoc_holidays` 手动覆盖列表作为兜底

### 3.2 ⚠️ 部分可替代：代码搜索

Tsanghi 的 `search_by_ticker` 支持模糊匹配和分页，用户输入部分代码即可搜索。TickFlow 的 `instruments.batch()` 需要精确的标的代码。

**影响**：用户在前端输入 ticker 搜索时，无法进行模糊匹配。替代方案：
- 前端增加代码格式提示，引导用户输入正确格式
- 通过 `tf.universes.get("CN_Equity_A")` 获取全部标的列表，前端本地过滤
- 利用 `tf.exchanges.get_instruments("SH")` 按交易所获取标的列表

### 3.3 代码格式差异

| | Tsanghi | TickFlow |
|---|---|---|
| A 股上交所 | `ticker` + `exchange_code=XSHG` | `600000.SH` |
| A 股深交所 | `ticker` + `exchange_code=XSHE` | `000001.SZ` |
| ETF | 同上 | `510300.SH` / `159915.SZ` |
| 美股 | 搜索返回 | `AAPL.US` |
| 港股 | 搜索返回 | `00700.HK` |

**影响**：整个代码处理链路需要适配，涉及 `DataService`、`helper.py` 中的 `determine_country` 函数、前端代码格式展示等。

### 3.4 认证方式差异

| | Tsanghi | TickFlow |
|---|---|---|
| 方式 | URL 参数 `?token=xxx` | Header `x-api-key` |
| Token 数量 | 2 个（按量+套餐） | 1 个 API Key |
| 失效处理 | 自动切换备用 Token | HTTP 401/403 |

**影响**：`BaseProvider` 和 `TokenManager` 的认证逻辑需要重写，但简化了多 Token 管理。

### 3.5 数据格式差异

**Tsanghi 响应**（行式）：
```json
{
  "code": 200,
  "data": [
    {"ticker": "510300", "date": "2025-01-15 09:30:00", "open": 3.5, "high": 3.51, ...}
  ]
}
```

**TickFlow 响应**（列式 CompactKlineData）：
```json
{
  "data": {
    "timestamp": [1736899200000, ...],
    "open": [3.5, ...],
    "high": [3.51, ...],
    "close": [3.505, ...],
    "volume": [10000, ...],
    "amount": [35000, ...]
  }
}
```

**影响**：`TsanghiProvider` 中所有数据解析逻辑需要重写。TickFlow SDK 已提供 `as_dataframe=True` 直接返回 DataFrame，但项目当前使用的解析方式（逐条 `KBar` 构建）需要适配。

### 3.6 套餐与计费差异

| | Tsanghi | TickFlow |
|---|---|---|
| 免费额度 | 需购买套餐 | 免费服务：日K线 + 标的信息 |
| 实时行情 | 按量计费 | 付费订阅 |
| 分钟 K 线 | 套餐内 | 付费订阅（仅 A 股） |
| 美股/港股分钟线 | 不支持 | **不支持**（仅日线） |

**影响**：TickFlow 的免费服务可用于开发测试，但生产环境需要付费。分钟 K 线仅支持 A 股，美股港股不能满足需求（不过当前项目仅聚焦 A 股 ETF）。

---

## 4. 架构改造评估

### 4.0 关键决策（已确认）

| # | 决策点 | 选定方案 |
|---|---|---|
| 1 | 代码搜索 | **本地标的池缓存过滤**：启动时拉取 `CN_ETF` 全量标的列表 → LRU 缓存 → 用户输入时本地过滤 |
| 2 | 代码格式转换 | **DataService 层透明转换**：`ticker + XSHG` ↔ `510300.SH`，上层无感知 |
| 3 | Provider 架构 | **保留抽象层**：新建 `TickFlowProvider`，与当前 `BaseProvider` 兼容 |
| 4 | 套餐选择 | **直接付费订阅**：分钟 K 线需付费，开发阶段即购买 |
| 5 | 缓存策略 | **保留文件缓存**：沿用 `FileCacheManager`，对 TickFlow SDK 返回值做 JSON 文件缓存 |
| 6 | 环境变量 | **`TICKFLOW_API_KEY`**：TickFlow SDK 默认读取此变量，`TickFlow()` 无参构造自动加载 |

### 4.1 环境变量定义

| 变量名 | 当前状态 | 迁移后 |
|---|---|---|
| `TSANGHI_TOKEN_01` | 按量计费 Token | ❌ 移除 |
| `TSANGHI_TOKEN_02` | 套餐计费 Token | ❌ 移除 |
| **`TICKFLOW_API_KEY`** | —（新增） | TickFlow SDK 自动读取，`TickFlow()` 无参即用 |

**本地调试 .env 加载约定：**

项目当前无 python-dotenv 依赖，环境变量依赖外部注入（Shell / Docker / Cloudflare Worker）。迁移方案约定新增 `python-dotenv` 作为开发依赖，本地启动时自动加载 `.env` 文件：

```python
# backend/app/__init__.py 或 app 工厂入口
from dotenv import load_dotenv
load_dotenv()  # 自动寻找项目根目录 .env 文件，文件不存在时静默跳过
```

```bash
# .env（gitignore，从 .env.example 复制）
TICKFLOW_API_KEY=tf_xxxxxxxxxxxxxxxxxxxxxxxx
# 可选：指定区域端点
# TICKFLOW_BASE_URL=https://hk-api.tickflow.org
```

**.env.example 文件已更新：** `backend/.env.example`，完整涵盖 TickFlow、数据库、JWT、Flask、CORS、日志等所有配置项，按分区注释。

**多环境注入对照：**

| 环境 | 注入方式 | 说明 |
|---|---|---|
| 本地开发 | `.env` + `python-dotenv` | `pip install python-dotenv`，app 入口 `load_dotenv()` |
| Cloudflare Worker | `wrangler secret put TICKFLOW_API_KEY` | 替换原有的 `TSANGHI_TOKEN_01/02` |
| Docker 部署 | `docker run -e TICKFLOW_API_KEY=xxx` | TickFlow SDK 自动读取 |

> TickFlow SDK 同时支持 `TICKFLOW_BASE_URL` 环境变量指定区域端点（如 `hk-api.tickflow.org`），默认使用 `https://api.tickflow.org`。

### 4.2 需要修改的文件

| 层 | 文件 | 改动量 | 说明 |
|---|---|---|---|
| 配置 | `config.yaml` | 中 | TickFlow API base_url、endpoint 定义、exchange_calendars 配置 |
| 配置 | `.env` / `.env.example` | 小 | `TICKFLOW_API_KEY` 替代 `TSANGHI_TOKEN_01` / `TSANGHI_TOKEN_02` |
| 新增 | `tickflow_provider.py` | **大** | 新建 Provider，封装 TickFlow SDK 调用 + 格式标准化 |
| Provider | `base_provider.py` | 中 | 认证逻辑从 URL Token 迁移到 Header `x-api-key` |
| Provider | `token_manager.py` | 小 | 简化：2 Token 多优先级 → 单 Key 管理 |
| Provider | `auth_strategies/` | 小 | URL Token 认证移除（不再适用） |
| Provider | `http_client.py` | 小 | 移除 Tsanghi 特定重试/Token 失效处理 |
| Service | `data_service.py` | **大** | 新增 `_format_symbol()` 代码转换；`search_by_ticker()` 改用本地缓存过滤；`get_trading_calendar()` 改用 `exchange_calendars`；底层调用从 `TsanghiProvider` 切换至 `TickFlowProvider` |
| Service | `backtest_service.py` | 小 | 交易日历调用不变（方法签名兼容） |
| Service | `etf_analysis_service.py` | 小 | 同上 |
| Utils | `helper.py` | 中 | 新增 `ticker_to_tickflow()` / `tickflow_to_ticker()` 格式转换函数 |
| Worker | `worker/src/index.ts` | 小 | 环境变量从 `TSANGHI_TOKEN_*` → `TICKFLOW_API_KEY` |
| Worker | `worker-configuration.d.ts` | 小 | 同上 |
| 清理 | `tsanghi_provider.py` | — | 移除 |
| 清理 | `url_token_auth.py` | — | 移除 |
| 数据模型 | `models.py` | — | KBar 结构不变 |

### 4.3 关键实现要点

**搜索：本地标的池缓存**
```python
# DataService 初始化时
self._universe_cache = {}
self._load_etf_universe()  # tf.universes.get("CN_ETF") → 1443 条
# search_by_ticker("510") → [sym for sym in self._etf_symbols if "510" in sym]
```

**代码格式转换（DataService 层）**
```python
# ticker="510300" + exchange_code="XSHG" → symbol="510300.SH"
# ticker="159915" + exchange_code="XSHE" → symbol="159915.SZ"
EXCHANGE_MAP = {"XSHG": "SH", "XSHE": "SZ", "XHKG": "HK", "XNYS": "US"}
```

**交易日历：exchange_calendars**
```python
xshg = xcals.get_calendar("XSHG")
dates = xshg.sessions_in_range("2024-01-01", "2024-12-31")
# DatetimeIndex(['2024-01-02', '2024-01-03', ...])
```

**缓存：保留 FileCacheManager**
```
cache/external_api/tickflow/<endpoint>/tickflow_<endpoint>_<md5hash>.json
```

### 4.4 预计工作量

| 模块 | 工作量 | 说明 |
|---|---|---|
| `tickflow_provider.py` | 2-3 人天 | 封装 SDK，标准化输出格式 |
| `data_service.py` 重构 | 1.5-2 人天 | 代码转换 + 搜索缓存 + 日历集成 |
| `config.yaml` / `.env` | 0.5 人天 | 新配置项定义 |
| `base_provider.py` / `token_manager.py` | 0.5 人天 | 认证简化 |
| `helper.py` 格式转换 | 0.3 人天 | ticker ↔ symbol 双向转换 |
| Worker 环境变量 | 0.2 人天 | 变量名替换 |
| 清理旧代码 | 0.5 人天 | 移除 Tsanghi 相关文件 |
| 测试验证 | 2-3 人天 | 单元 + 集成 + 数据对比 |
| **总计** | **约 7.5-10 人天** | |

---

## 5. TickFlow 的额外优势

1. **免费服务层**：`TickFlow.free()` 提供日 K 线 + 标的信息，开发测试零成本
2. **批量接口**：`klines.batch()` 一次请求获取多只标的，效率远高于单只循环
3. **复权支持**：5 种复权方式（Tsanghi 不支持复权），对回测更友好
4. **WebSocket 推送**：实时行情推送能力，未来可扩展实时监控
5. **官方 Python SDK**：`pip install tickflow[all]`，开箱即用
6. **多区域节点**：hk-api / sg-api / us-api 可选，网络更稳定
7. **财务数据**：利润表、资产负债表等（需 Expert 套餐），扩展性强
8. **五档盘口**：市场深度数据（需 Pro/Expert）

---

## 6. 结论与建议

### 6.1 总体评估

**可以替换，且交易日历问题已通过 `exchange_calendars` 解决。** 推荐采用**一步到位的完全替换方案**，无需保留 Tsanghi。

### 6.2 核心障碍

| 障碍 | 严重程度 | 解决方案 |
|---|---|---|
| ~~交易日历 API 缺失~~ | 🟢 已解决 | `exchange_calendars` 离线库（XSHG/XHKG/XNYS 三市场） |
| 模糊搜索缺失 | 🟡 中等 | 前端本地过滤 + 标的池缓存 |
| 代码格式不一致 | 🟡 中等 | 统一适配层转换 |
| 美股港股分钟线不支持 | 🟢 低 | 当前项目仅聚焦 A 股 ETF |

### 6.3 推荐方案：直接完全替换

**TickFlow + exchange_calendars（无 Tsanghi 依赖）**

| 模块 | 数据源 | 说明 |
|---|---|---|
| 行情数据（实时/日线/5分钟） | `TickFlow` Python SDK | 付费订阅，直接调用 SDK |
| 交易日历（A股/港股/美股） | `exchange_calendars` 离线库 | `pip install` 即用，零网络依赖 |
| 代码搜索 | TickFlow `universes.get("CN_ETF")` | 启动时拉取全量 ETF 列表 → LRU 缓存 → 本地过滤 |
| 代码格式转换 | DataService 层 `_format_symbol()` | `ticker+XSHG` ↔ `510300.SH` 透明双向转换 |
| Provider 架构 | 新建 `TickFlowProvider` | 保留 BaseProvider 抽象，兼容现有调用链 |
| 缓存 | 保留 `FileCacheManager` | 对 SDK 返回值做 JSON 文件缓存，TTL 不变 |

- 完全移除 Tsanghi 依赖（不再需要 `TSANGHI_TOKEN_01/02`）
- 仅需维护 1 个 API Key（`TICKFLOW_API_KEY`）
- 预期工作量：约 7.5-10 人天

**与之前"混合数据源方案"对比：**

| | 混合方案（旧） | 完全替换（新推荐） |
|---|---|---|
| 交易日历 | 保留 Tsanghi | `exchange_calendars` |
| Tsanghi 依赖 | 仍然存在 | **完全移除** |
| API Token 管理 | 3 套（TFlow + T01 + T02） | 1 套（TFlow API Key） |
| 网络依赖 | 两方都可能出问题 | TickFlow 一方 + 离线库零网络 |
| 后续维护 | 两套 Provider 代码 | 仅 TickFlowProvider |

**后续可选增强：**
- 接入 TickFlow WebSocket 实时行情推送
- 利用复权数据进行更精准的回测
- 引入财务数据做基本面筛选
- 扩展港股/美股回测（`exchange_calendars` 已包含 XHKG/XNYS）

### 6.4 风险提示

1. **数据一致性**：两个数据源的价格可能存在微小差异，切换后回测结果可能与历史不一致
2. **API 稳定性**：TickFlow 为较新的服务（GitHub 仓库创建于 2026-03），长期稳定性待验证
3. **离线库滞后**：`exchange_calendars` 遇到突发的临时休市需等社区更新，虽概率极低但可通过 `adhoc_holidays` 配置兜底
4. **分钟线仅 A 股**：若未来扩展美股/港股回测，TickFlow 无法提供分钟线
5. **intraday 为 Beta**：文档标注日内分钟线接口为 Beta 版本，可能有变更

---

## 附录 A：API 端点对比表

| 功能 | Tsanghi API | TickFlow API | 兼容 |
|---|---|---|---|
| 交易所列表 | `GET /fin/stock/exchange` | `tf.exchanges` / `tf.universes.list()` | ✅ |
| 交易日历 | `GET /fin/stock/{exchange}/market/calendar` | `exchange_calendars` 离线库 (XSHG/XHKG/XNYS) | ✅ |
| 代码搜索 | `GET /fin/search/list` | `POST /v1/instruments` (精确) | ⚠️ |
| 实时行情 | `GET /fin/stock/{exchange}/realtime` | `POST /v1/quotes` | ✅ |
| 日 K 线 | `GET /fin/stock/{exchange}/daily` | `GET /v1/klines?period=1d` | ✅ |
| 5 分钟 K 线 | `GET /fin/stock/{exchange}/5min` | `GET /v1/klines?period=5m` | ✅ |
| 批量 K 线 | — | `POST /v1/klines/batch` | ➕ |
| 日内分时 | — | `GET /v1/klines/intraday` | ➕ |
| 复权 K 线 | — | `adjust` 参数 | ➕ |
| WebSocket | — | `/v1/ws/stream` | ➕ |
| 财务数据 | — | `tf.financials.*` | ➕ |
| 五档盘口 | — | `tf.depth.get()` | ➕ |

## 附录 B：核心代码文件索引

| 文件 | 路径 |
|---|---|
| Tsanghi Provider | `backend/app/external/providers/tsanghi_provider.py` |
| Base Provider | `backend/app/external/base_provider.py` |
| Token Manager | `backend/app/external/token_manager.py` |
| Auth Strategy | `backend/app/external/auth_strategies/url_token_auth.py` |
| HTTP Client | `backend/app/external/http_client.py` |
| Config | `backend/app/config/config.yaml` |
| Env | `backend/.env` |
| Data Service | `backend/app/services/data_service.py` |
| Backtest Service | `backend/app/services/backtest_service.py` |
| ETF Analysis | `backend/app/services/etf_analysis_service.py` |
| Helper | `backend/app/utils/helper.py` |
| Worker Config | `worker/worker-configuration.d.ts` |
