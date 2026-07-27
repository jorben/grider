# Grider - ETF/股票 网格交易策略分析工具（AkShare 免费数据版）

🎯 一个网格交易策略分析与回测工具：基于 ATR 算法计算网格参数、评估标的适宜度、做历史回测。

> 本版本基于开源项目 [jorben/grider](https://github.com/jorben/grider)（Apache-2.0）改造，
> **数据源由付费的 Tsanghi 替换为免费的 [AkShare](https://akshare.akfamily.xyz/)**（东方财富 / 新浪公开行情），
> **无需任何 token、无到期、不花钱**。前端已预编译并由后端托管，运行时**只需 Python，无需 Node**。

---

## ✨ 主要特性

- **免费数据**：AkShare（新浪为主源、东方财富兜底），支持 A 股、ETF（个股也支持）
- **ATR 智能网格**：等差/等比网格、适宜度 4 维评分、参数智能建议
- **网格标的筛选器**：一键对约 50 只主流 ETF 批量评分并按适宜度排序，快速挑出适合网格的标的
- **均线策略回测**：趋势跟随（SMA/EMA、周期可选、仓位可配），与网格策略互补对比
- **专业回测**：收益率/最大回撤/夏普比率、交易记录明细、Excel 导出
- **分析前可自定义参数**：首页勾选即可在分析后直接编辑价格区间/步长/单笔数量/回测区间
- **单端口部署**：后端同时托管前端页面，浏览器访问一个地址即可

---

## 🚀 快速开始（一键启动）

### 前提：装一次 Python（免费）
- Windows：https://www.python.org/downloads/ （安装时勾选 **Add Python to PATH**）
- macOS：`brew install python` 或 https://www.python.org/downloads/macos/

### 获取代码
```bash
git clone https://github.com/vickingwu/grider.git
cd grider
```

### 启动
- **Windows**：双击 `start.bat`
- **macOS**：先 `chmod +x start.command`，然后双击 `start.command`（或终端 `./start.command`）

脚本会自动：检测 Python → 首次创建虚拟环境并安装依赖（约 2-5 分钟）→ 启动服务 → 自动打开浏览器。

启动完成后访问：**http://127.0.0.1:5000**

> 关闭弹出的命令行/终端窗口即可停止服务。

---

## 🧰 手动启动（脚本不可用时）

**Windows**
```bat
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
set FLASK_ENV=production
.venv\Scripts\python.exe main.py --port 5000 --host 127.0.0.1
```

**macOS / Linux**
```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export FLASK_ENV=production
.venv/bin/python main.py --port 5000 --host 127.0.0.1
```
然后浏览器打开 http://127.0.0.1:5000

---

## 🔍 网格标的筛选器

不知道选哪个标的？用筛选器一键挑选。

- **入口**：首页右上角「网格标的筛选器」按钮 → `/screener` 页面。
- **做什么**：对约 50 只主流 ETF（宽基 / 行业 / 跨境 / 红利 / 商品债券）逐个跑**与详情页完全一致**的适宜度评分，按总分从高到低排序成表格。
- **评分维度**（满分 100）：振幅 ATR(35) + 波动率(30) + 市场特征 ADX(25) + 流动性(10)。
  - ≥70 非常适合 / 60~70 基本适合 / <60 不适合。
  - 适合网格的标的特征：天天震荡（ATR≥2%）、年化波动率 15%~45%、不走单边趋势（ADX<20）、成交活跃。
- **表格内容**：排名、代码、名称、分类、总分、ATR%、波动率%、ADX、日均成交额、结论；支持按分类筛选，每行可直接跳转到详细分析。
- **性能**：全候选池约 12~15 秒完成（受免费数据源速度影响），结果缓存 1 小时，二次打开秒出；可点「强制刷新数据」重算。
- **自定义候选池**：直接编辑 `backend/app/constants.py` 里的 `SCREENER_CANDIDATES` 列表（增减代码即可，前端无需改动）。

---

## 📈 均线策略回测

与网格策略互补的另一种回测方式。

- **入口**：首页右上角「均线策略回测」按钮 → `/ma-backtest` 独立页面（不走网格分析流程）。
- **策略逻辑**：趋势跟随——收盘价**上穿**所选均线视为金叉买入，**下穿**视为死叉清仓。
  - 与网格相反：网格适合**震荡**行情（低买高卖），均线适合**趋势**行情（追涨杀跌）。
- **参数**：
  - 均线类型：SMA（简单）/ EMA（指数）
  - 均线周期：5 / 20 / 50 / 99 / 128 / 225 日，或自定义（2~500）
  - 买入仓位比例：10%~100%（默认满仓）
  - 回测区间：可选，留空默认最近半年；跨度超 120 天自动用日线
- **结果**：收益/持有对比/超额/年化/回撤/夏普/交易次数/胜率 + 价格·均线·买卖点叠加图 + 交易记录表。

> 💡 **长周期均线无需手动拉长区间**：选 128/225 日等长周期均线时，后端会自动在回测开始日之前
> 额外多取相应天数的"预热数据"来计算均线（这段数据只用于喂均线，不参与买卖与收益统计），
> 因此即使回测区间只有近半年，长周期均线也能在区间首日就有值，不会报错。

> 提示：均线在**震荡行情**里会被反复触发（俗称"被洗"），收益可能不如持有；在**单边趋势**里优势明显。建议多换几个周期对比。

---

## 🏗️ 技术架构

```
前端：React 18 + Vite + Tailwind + Recharts（已预编译到 static/）
后端：Flask (Python 3.10+) + pandas
数据：AkShare（新浪主源 / 东方财富兜底，带本地缓存）
```

目录结构（简要）：
```
grider/
├── backend/          # Flask 后端 + 算法 + AkShare 数据层
│   ├── app/services/data_service.py   # 数据获取（AkShare）
│   ├── app/algorithms/                # ATR / 网格 / 回测算法
│   └── main.py
├── frontend/         # React 源码（开发用）
├── static/           # 预编译前端（生产运行用，后端托管）
├── start.bat         # Windows 一键启动
├── start.command     # macOS 一键启动
└── SETUP.md          # 详细安装/排错说明
```

---

## ❓ 常见问题

- **日志刷 “Connection aborted / 调用失败”**：正常现象。主数据源（东方财富）偶发限流，
  系统会自动切换到新浪兜底，不影响结果。
- **个股名称首次显示成代码**：首次下载名称表约十几秒，之后缓存到 `backend/cache/`（重启复用）。
- **端口被占用**：换端口启动（如 `--port 5001`），浏览器用对应端口访问。
- **修改了前端源码想生效**：需在 `frontend/` 执行 `npm install && npm run build`，
  再把 `frontend/dist` 覆盖到根目录 `static/`（仅此场景需要 Node）。

更多细节见 [SETUP.md](SETUP.md)。

---

## ⚠️ 风险提示

本工具所有数据与分析结果**仅供学习研究，不构成任何投资建议**。
网格交易可能面临持续下跌风险，历史回测不代表未来表现。投资有风险，决策需谨慎。

---

## 📜 许可证

本项目基于 [jorben/grider](https://github.com/jorben/grider) 改造，遵循 **Apache 2.0** 许可证，详见 [LICENSE](LICENSE)。
