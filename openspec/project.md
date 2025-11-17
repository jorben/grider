# Project Context

## Purpose
Grider (Grid Trading Assistant) 是一个网格交易策略分析和回测系统,帮助用户评估网格交易策略的历史表现。系统基于真实的历史K线数据模拟策略执行,计算收益、风险等多维度指标,为交易决策提供数据支持。

**核心功能:**
- 网格交易策略配置与优化
- 历史数据回测分析
- 多维度性能指标计算(收益率、夏普比率、最大回撤等)
- 可视化交易记录和收益曲线
- 基准对比(与持有不动策略对比)

## Tech Stack

### 后端 (Backend)
- **语言:** Python 3.13+
- **框架:** Flask 3.1.2
- **数据库:** SQLAlchemy + Flask-Migrate
- **认证:** Flask-JWT-Extended
- **数据处理:** Pandas 2.3.3
- **服务器:** Gunicorn + Gevent
- **其他:** Flask-CORS, Marshmallow, PyYAML, python-dotenv

### 前端 (Frontend)
- **框架:** React 18.2.0
- **构建工具:** Vite 5.0.8
- **路由:** React Router DOM 7.9.1
- **样式:** Tailwind CSS 3.3.6 + PostCSS + Autoprefixer
- **图表:** Recharts 3.2.1
- **HTTP客户端:** Axios 1.6.0
- **图标:** Lucide React 0.294.0
- **工具库:** clsx 2.0.0
- **其他:** react-helmet-async 2.0.5

### 开发工具
- **包管理:** uv (Python), npm (JavaScript)
- **代码质量:** ESLint, Prettier
- **容器化:** Docker + Docker Compose
- **版本控制:** Git

## Project Conventions

### Code Style
- **Python:** 遵循PEP 8规范
- **JavaScript/React:** ESLint配置,使用React hooks模式
- **格式化:** 前端使用Prettier自动格式化
- **命名约定:**
  - Python: snake_case (函数、变量), PascalCase (类)
  - JavaScript: camelCase (函数、变量), PascalCase (组件)

### Architecture Patterns
- **后端架构:**
  - 蓝图(Blueprint)模式组织路由
  - 服务层(Services)处理业务逻辑
  - 模型层(Models)定义数据结构
  - 中间件(Middleware)处理横切关注点
  - 算法层(Algorithms)实现交易策略和回测逻辑

- **前端架构:**
  - 功能模块化组织(Features-based structure)
  - 共享组件(Shared components)
  - 页面级组件(Pages)
  - 路径别名: `@/*`, `@shared/*`, `@features/*`, `@pages/*`, `@app/*`

- **环境隔离:**
  - 开发环境: 前后端分离运行
  - 生产环境: Flask提供静态文件服务

### Testing Strategy
- **后端测试:** pytest + pytest-flask
- **测试范围:**
  - 单元测试(算法、服务层)
  - API集成测试
- **回测验证:** 基于历史K线数据验证策略逻辑

### Git Workflow
- **主分支:** master
- **版本管理:** 遵循语义化版本(Semantic Versioning)
- **提交规范:**
  - feat: 新功能
  - fix: Bug修复
  - refactor: 重构
  - perf: 性能优化
  - chore: 构建/工具变更
  - docs: 文档更新
- **变更日志:** 自动生成CHANGELOG.md
- **发布流程:** 参考 docs/release_checklist.md

## Domain Context

### 网格交易策略
网格交易是一种量化交易策略,在价格区间内设置多个买卖网格,当价格触及网格线时自动执行买卖操作。

**关键概念:**
- **网格间距:** 相邻网格之间的价格差
- **网格数量:** 总共设置的网格层数
- **价格区间:** 网格策略的有效价格范围
- **网格触发率:** 实际触发的网格数/总网格数
- **配对交易:** 买入和卖出配对的交易
- **胜率:** 盈利交易次数/总交易次数

### 回测指标
- **总收益率:** (期末资产 - 期初资产) / 期初资产
- **年化收益率:** 按年化计算的收益率
- **最大回撤:** 从最高点到最低点的最大跌幅
- **夏普比率:** 风险调整后的收益率指标
- **盈亏比:** 平均盈利/平均亏损
- **资金利用率:** 已使用资金/总资金

### 数据来源
- 历史K线数据(股票/ETF)
- 交易日历数据
- 行情数据提供商API

## Important Constraints

### 技术约束
- Python版本要求: >= 3.13
- 回测数据范围: 最近30个交易日
- 图表数据采样: 最多800个数据点
- SessionStorage配额管理: 需处理存储限制

### 业务约束
- 回测结果仅供参考,不构成投资建议
- 手续费默认: 0.02%, 最低5元
- 无风险利率默认: 3%
- 年交易日数: 244天

### 合规约束
- 需要用户登录认证(JWT)
- API访问需要密钥配置
- 敏感配置通过环境变量管理

## External Dependencies

### 数据提供商
- 行情数据API (需配置密钥)
- K线历史数据接口
- 交易日历服务

### 基础设施
- 数据库: SQLite(开发) / PostgreSQL(生产可选)
- 静态文件存储: 本地文件系统
- 缓存: 内存缓存(TTL可配置)
