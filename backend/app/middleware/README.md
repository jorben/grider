# 中间件模块说明

## 概述

本模块提供了Flask应用的中间件功能，包括CORS跨域支持、中间件注册管理等。

## 目录结构

```
app/middleware/
├── __init__.py      # 模块导出
├── cors.py          # CORS中间件配置
├── registry.py      # 中间件注册器
└── README.md        # 说明文档
```

## 功能特性

### 1. CORS中间件

提供跨域资源共享支持，支持以下配置：

- **CORS_ORIGINS**: 允许的跨域来源（默认：`*`）
- **CORS_METHODS**: 允许的HTTP方法（默认：`GET,POST,PUT,DELETE,OPTIONS`）
- **CORS_HEADERS**: 允许的请求头（默认：`Content-Type,Authorization`）
- **CORS_SUPPORTS_CREDENTIALS**: 是否支持凭据（默认：`false`）

### 2. 中间件注册器

提供统一的中间件注册和管理机制：

- 自动注册中间件
- 按注册顺序应用中间件
- 错误处理机制
- 中间件状态查询

## 使用方法

### 基本配置

在Flask应用工厂中自动集成：

```python
from app import create_app

app = create_app()  # 自动注册所有中间件
```

### 环境变量配置

在`.env`文件中配置CORS：

```env
# CORS配置
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=Content-Type,Authorization,X-Requested-With
CORS_SUPPORTS_CREDENTIALS=false
```

### 自定义中间件注册

要添加新的中间件，在`registry.py`中注册：

```python
from app.middleware.registry import register_middleware

def my_custom_middleware(app):
    # 中间件逻辑
    return app

# 注册中间件
register_middleware(my_custom_middleware)
```

## API参考

### `setup_cors(app)`

配置CORS中间件。

**参数：**
- `app`: Flask应用实例

**返回：**
- 配置了CORS的Flask应用实例

### `register_middleware(middleware_func)`

注册中间件函数。

**参数：**
- `middleware_func`: 中间件函数，接收Flask应用并返回配置后的应用

### `register_middlewares(app)`

注册所有已配置的中间件。

**参数：**
- `app`: Flask应用实例

**返回：**
- 配置了所有中间件的Flask应用实例

### `get_registered_middlewares()`

获取已注册的中间件列表。

**返回：**
- 中间件函数名列表

## 测试

项目使用pytest进行测试，测试文件位于`tests/`目录下。

### 运行测试

运行所有测试：
```bash
uv run pytest
```

运行中间件相关测试：
```bash
uv run pytest tests/test_middleware.py -v
```

### 测试覆盖范围

- **中间件注册器测试**：验证中间件注册和管理功能
- **CORS中间件测试**：验证CORS头设置和预检请求处理
- **错误处理测试**：验证中间件错误处理机制

### 测试结构

```
tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # pytest配置和fixtures
└── test_middleware.py   # 中间件功能测试
```

### 测试示例

测试用例遵循pytest规范，使用fixtures管理测试环境：

```python
def test_cors_middleware_integration(client):
    """测试CORS中间件集成"""
    response = client.options('/api/user/hello')
    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' in response.headers
```

## 部署说明

1. 生产环境建议配置具体的CORS来源，避免使用`*`
2. 根据前端应用的实际需求调整CORS配置
3. 监控中间件的性能影响

## 故障排除

### CORS头未生效

1. 检查环境变量配置是否正确
2. 确认中间件注册顺序
3. 验证Flask应用配置

### 中间件注册失败

1. 检查中间件函数签名
2. 查看应用日志获取详细错误信息
3. 确认依赖包已正确安装

## 扩展开发

要添加新的中间件功能：

1. 在`middleware`目录下创建新的中间件文件
2. 实现中间件函数
3. 在`registry.py`中注册
4. 更新`__init__.py`导出
5. 编写测试用例