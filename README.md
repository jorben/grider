# Grider - ETF网格交易策略分析工具

[![Version](https://img.shields.io/github/release/jorben/grider.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

🎯 **Grider** 是一个专业的ETF网格交易策略分析工具，提供全面的回测功能、智能参数优化和多市场支持。帮助投资者量化分析网格交易策略的表现，优化投资决策。

## ✨ 核心特性

### 🚀 网格交易策略分析
- **智能网格计算**：支持等差网格和等比网格两种策略
- **ATR动态网格**：基于平均真实波动率的动态网格调整
- **多参数优化**：网格数量、风险系数、调整系数等参数智能建议
- **风险评估**：内置风险模型和适宜度评分系统

### 📊 专业回测系统
- **历史数据回测**：支持30-120个交易日的详细回测分析
- **实时交易模拟**：精确模拟网格交易的买入卖出逻辑
- **性能指标分析**：收益率、最大回撤、夏普比率等专业指标
- **交易记录明细**：完整的交易历史记录和Excel导出功能

### 🌍 多市场支持
- **A股市场**：沪深股票和ETF支持
- **港股市场**：香港ETF和股票数据
- **美股市场**：美国ETF和股票支持
- **实时行情**：集成多家数据源，确保数据准确性

### 💻 现代化界面
- **响应式设计**：完美适配桌面端和移动端
- **交互式图表**：基于Recharts的丰富数据可视化
- **实时更新**：数据自动刷新和缓存优化
- **用户友好**：直观的操作界面和详细的使用指导

## 🏗️ 技术架构

### 前端技术栈
```
React 18.2.0          # 现代化React框架
Vite 5.0.8            # 快速构建工具
Tailwind CSS 3.3.6    # 原子化CSS框架
Recharts 3.2.1        # 数据可视化库
Axios 1.6.0           # HTTP客户端
Lucide React          # 现代化图标库
```

### 后端技术栈
```
Flask                 # Python Web框架
Python 3.13+          # 现代化Python版本
```

### 部署支持
```
Docker                # 容器化部署
Gunicorn              # 生产级WSGI服务器
```

## 🚀 快速开始

### 环境要求
- Node.js 18.0+
- Python 3.8+
- Docker (可选)

### 使用Docker部署（推荐）

```bash
# 克隆项目
git clone https://github.com/jorben/grider.git
cd grider

# 构建并启动服务
docker-compose up -d

# 访问应用
open http://localhost:5000
```

### 本地开发部署

#### 1. 克隆项目
```bash
git clone https://github.com/jorben/grider.git
cd grider
```

#### 2. 后端设置
```bash
cd backend
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的API密钥

# 启动后端服务
uv run main.py
```

#### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

#### 4. 访问应用
- 开发环境：http://localhost:3000
- 生产环境：http://localhost:5000

## ⚙️ 配置说明

### 环境变量配置

在 `backend/.env` 文件中配置以下变量：

```env
# 应用配置
FLASK_ENV=development
FLASK_PORT=5000
FLASK_HOST=0.0.0.0


# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=logs

# 外部API配置
TSANGHI_API_KEY=your-tsanghi-api-key
# 其他API密钥...
```

### 数据源配置

项目支持多个数据源，需要在环境变量中配置相应的API密钥：

- **Tsanghi API**: 主要的股票和ETF数据源
- **其他数据源**: 可配置备用数据源

## 📖 使用指南

### 1. 选择ETF产品
- 在搜索框中输入ETF代码或名称
- 支持A股、港股、美股市场的ETF
- 查看ETF的基本信息和历史表现

### 2. 配置网格参数
- **投资资金**: 设置网格交易的总资金
- **网格类型**: 选择等差网格或等比网格
- **网格数量**: 设置网格的层数（建议5-20层）
- **风险系数**: 调整策略的风险偏好
- **调整系数**: 微调网格参数

### 3. 查看分析报告
- **策略概述**: 查看网格策略的基本参数和建议
- **风险评估**: 了解策略的风险等级和适宜度
- **回测结果**: 查看历史回测的交易记录和收益表现
- **性能指标**: 分析收益率、最大回撤等关键指标

### 4. 导出和分享
- 支持将回测结果导出为Excel文件
- 可生成分析报告的分享链接
- 支持打印和PDF导出功能

## 🧪 测试

### 运行后端测试
```bash
cd backend
python -m pytest tests/ -v
```

### 运行前端测试
```bash
cd frontend
npm test
```

### 代码质量检查
```bash
# 后端代码检查
cd backend
flake8 app/
mypy app/

# 前端代码检查
cd frontend
npm run lint
npm run lint:fix
```

## 📁 项目结构

```
grider/
├── frontend/                 # 前端React应用
│   ├── src/
│   │   ├── app/             # 应用主框架
│   │   ├── features/        # 功能模块
│   │   │   ├── analysis/    # 分析功能
│   │   │   ├── etf/         # ETF选择
│   │   │   └── history/     # 历史记录
│   │   ├── shared/          # 共享组件和工具
│   │   └── pages/           # 页面组件
│   ├── public/              # 静态资源
│   └── package.json
├── backend/                 # 后端Flask应用
│   ├── app/
│   │   ├── algorithms/      # 算法模块
│   │   │   ├── grid/        # 网格算法
│   │   │   └── atr/         # ATR计算
│   │   ├── external/        # 外部API集成
│   │   ├── models/          # 数据模型
│   │   ├── routes/          # API路由
│   │   ├── services/        # 业务服务
│   │   └── utils/           # 工具函数
│   ├── cache/               # 缓存目录
│   ├── logs/                # 日志目录
│   └── main.py
├── CHANGELOG.md             # 更新日志
├── Dockerfile              # Docker配置
├── docker-compose.yml      # Docker Compose配置
└── README.md               # 项目文档
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- 前端：使用 ESLint 和 Prettier
- 后端：遵循 PEP 8 规范
- 提交信息：使用 Conventional Commits 格式

## 📄 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本更新记录。

### 最新版本 (1.3.0)
- ✨ 实现自定义网格参数回测功能
- 🔧 合并网格参数和回测参数设置面板
- 🐛 修复已知问题并优化用户体验

## ⚠️ 风险提示

**投资有风险，入市需谨慎**

本工具提供的所有分析和建议仅供参考，不构成投资建议：

- 网格交易策略可能面临持续下跌的风险
- 历史回测结果不代表未来表现
- 市场波动可能导致实际收益与预期存在差异
- 建议在充分了解风险的前提下谨慎投资

## 📞 支持与反馈

- **GitHub Issues**: [提交问题](https://github.com/jorben/grider/issues)
- **功能建议**: [功能请求](https://github.com/jorben/grider/discussions)
- **邮件联系**: [发送邮件](mailto:jorben@aix.me)

## 📜 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和服务：

- [React](https://reactjs.org/) - 用户界面框架
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Recharts](https://recharts.org/) - 数据可视化
- [Tailwind CSS](https://tailwindcss.com/) - CSS框架
- 以及所有为开源社区做出贡献的开发者们

---

<div align="center">

**🚀 如果这个项目对您有帮助，请给我们一个 Star！**

Made with ❤️ by [Jorben](https://github.com/jorben/grider)

</div>