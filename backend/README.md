# Flask 后端项目

基于 Flask 的 RESTful API 后端项目，支持用户管理、JWT认证、数据库迁移等功能。

## 项目特性

- ✅ Flask 应用工厂模式
- ✅ SQLAlchemy ORM 数据库操作
- ✅ Flask-Migrate 数据库迁移
- ✅ Flask-JWT-Extended JWT 认证
- ✅ CORS 跨域支持
- ✅ 结构化日志系统（JSON/TEXT格式）
- ✅ 自动数据库迁移
- ✅ 环境变量配置管理

## 快速开始

### 环境要求

- Python 3.8+
- uv（Python包管理工具）

### 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

### 运行应用

```bash
# 使用 uv 运行应用
uv run python main.py
```

应用将在 `http://localhost:5000` 启动。

## 日志系统

项目集成了功能强大的日志系统，支持多种配置选项。

### 日志配置说明

在 `.env` 文件中配置日志参数：

```env
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志目录
LOG_DIR=logs

# 日志格式：json 或 text
LOG_FORMAT=json

# 日志文件保留天数
LOG_BACKUP_COUNT=30

# 是否开启console输出
LOG_TO_CONSOLE=true
```

### 日志格式

#### JSON 格式（推荐生产环境）
```json
{
  "timestamp": "2025-10-01T14:06:48.952241Z",
  "level": "INFO",
  "logger": "app",
  "module": "logger",
  "function": "setup_logger",
  "line": 114,
  "message": "日志系统已初始化"
}
```

**优点**：
- 结构化数据，易于解析
- 便于日志分析系统（如ELK、Splunk）处理
- 支持复杂查询和过滤

#### TEXT 格式（推荐开发环境）
```
2025-10-01 22:06:48 - app - INFO - [logger:setup_logger:114] - 日志系统已初始化
```

**优点**：
- 人类可读性强
- 便于开发调试
- 简洁直观

### 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发环境，详细的程序执行信息 |
| INFO | 一般信息 | 正常的程序运行信息 |
| WARNING | 警告信息 | 潜在问题，但不影响程序运行 |
| ERROR | 错误信息 | 程序出错但可以继续运行 |
| CRITICAL | 严重错误 | 程序无法继续运行的严重错误 |

### 在代码中使用日志

#### 在路由或视图中
```python
from flask import current_app

@app.route('/example')
def example():
    current_app.logger.info('处理示例请求')
    current_app.logger.debug(f'请求参数: {request.args}')
    
    try:
        # 业务逻辑
        result = process_data()
        current_app.logger.info('请求处理成功')
        return result
    except Exception as e:
        current_app.logger.error(f'处理失败: {str(e)}', exc_info=True)
        return {'error': str(e)}, 500
```

#### 在服务层或工具函数中
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

def some_function():
    logger.info('执行某个功能')
    logger.warning('发现潜在问题')
    logger.error('发生错误')
```

### 日志轮转策略

- **轮转方式**：按天轮转（每天午夜自动创建新文件）
- **文件命名**：`app.log.2025-10-01.log`
- **保留天数**：根据 `LOG_BACKUP_COUNT` 配置（默认30天）
- **自动清理**：超过保留天数的日志文件自动删除

### 日志文件位置

日志文件存储在 `logs/` 目录下：
- 当前日志：`logs/app.log`
- 历史日志：`logs/app.log.YYYY-MM-DD.log`

## 数据库

### 数据库配置

在 `.env` 文件中配置数据库URL：

```env
# SQLite（默认）
DATABASE_URL=sqlite:///app.db

# PostgreSQL
# DATABASE_URL=postgresql://username:password@localhost/dbname

# MySQL
# DATABASE_URL=mysql://username:password@localhost/dbname
```

### 数据库迁移

应用启动时会自动执行数据库迁移。手动执行迁移命令：

```bash
# 创建迁移
uv run flask db migrate -m "描述信息"

# 应用迁移
uv run flask db upgrade

# 回滚迁移
uv run flask db downgrade
```

## JWT 认证

### 配置

```env
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**⚠️ 安全提示**：生产环境请使用强密码生成器生成安全的密钥。

### 使用示例

```python
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# 创建 token
@app.route('/login', methods=['POST'])
def login():
    # 验证用户
    access_token = create_access_token(identity=user.id)
    return {'access_token': access_token}

# 保护路由
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return {'user_id': current_user_id}
```

## CORS 配置

在 `.env` 文件中配置CORS：

```env
# 允许的跨域来源
CORS_ORIGINS=*

# 允许的HTTP方法
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS

# 允许的请求头
CORS_HEADERS=Content-Type,Authorization

# 是否支持凭据
CORS_SUPPORTS_CREDENTIALS=false
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── constants.py         # 常量定义
│   ├── middleware/          # 中间件
│   │   ├── __init__.py
│   │   └── cors.py         # CORS中间件
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   └── user.py         # 用户模型
│   ├── routes/             # 路由蓝图
│   │   ├── __init__.py
│   │   └── demo_routes.py  # 示例路由
│   ├── services/           # 业务逻辑
│   │   └── user_service.py # 用户服务
│   └── utils/              # 工具函数
│       ├── __init__.py
│       ├── logger.py       # 日志配置
│       └── validation.py   # 数据验证
├── logs/                   # 日志目录
├── migrations/             # 数据库迁移
├── tests/                  # 测试文件
├── .env                    # 环境变量（不提交到版本控制）
├── .env.example            # 环境变量示例
├── main.py                 # 应用入口
├── pyproject.toml          # 项目配置
└── README.md              # 项目文档
```

## 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_validation.py

# 运行测试并显示覆盖率
uv run pytest --cov=app tests/
```

## 开发建议

### 日志最佳实践

1. **选择合适的日志级别**
   - 开发环境：使用 `DEBUG` 级别获取详细信息
   - 生产环境：使用 `INFO` 或 `WARNING` 级别

2. **使用结构化日志**
   - 生产环境推荐使用 `json` 格式
   - 便于日志分析和监控

3. **记录关键信息**
   - 请求处理的开始和结束
   - 重要的业务操作
   - 异常和错误详情

4. **性能考虑**
   - 避免在循环中大量记录日志
   - 使用适当的日志级别过滤信息

### 代码规范

- 使用类型提示提高代码可读性
- 遵循 PEP 8 编码规范
- 编写单元测试确保代码质量
- 使用蓝图组织路由
- 实现清晰的关注点分离

## 部署

### 生产环境配置

1. **环境变量**
```env
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=WARNING
LOG_FORMAT=json
JWT_SECRET_KEY=<strong-random-key>
```

2. **使用 Gunicorn 运行**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "main:app"
```

3. **日志监控**
   - 配置日志收集系统（如 ELK Stack）
   - 设置日志告警规则
   - 定期检查日志文件大小


## 贡献指南

欢迎提交 Issue 和 Pull Request！