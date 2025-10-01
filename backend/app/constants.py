"""
常量模块
集中管理应用中的所有常量，便于维护和统一管理
"""

from typing import Final

# ============================================================================
# 应用配置常量
# ============================================================================

# 应用名称和版本
APP_NAME: Final[str] = "Grider Backend"
APP_VERSION: Final[str] = "1.0.0"
API_VERSION: Final[str] = "v1"

# 环境类型
ENV_DEVELOPMENT: Final[str] = "development"
ENV_PRODUCTION: Final[str] = "production"
ENV_TESTING: Final[str] = "testing"

# 默认配置值
DEFAULT_DATABASE_URL: Final[str] = "sqlite:///app.db"
DEFAULT_JWT_SECRET_KEY: Final[str] = "your-secret-key-change-in-production"
DEFAULT_PORT: Final[int] = 5000
DEFAULT_HOST: Final[str] = "127.0.0.1"

# ============================================================================
# HTTP 状态码常量
# ============================================================================

# 成功状态码
HTTP_OK: Final[int] = 200
HTTP_CREATED: Final[int] = 201
HTTP_ACCEPTED: Final[int] = 202
HTTP_NO_CONTENT: Final[int] = 204

# 客户端错误状态码
HTTP_BAD_REQUEST: Final[int] = 400
HTTP_UNAUTHORIZED: Final[int] = 401
HTTP_FORBIDDEN: Final[int] = 403
HTTP_NOT_FOUND: Final[int] = 404
HTTP_METHOD_NOT_ALLOWED: Final[int] = 405
HTTP_CONFLICT: Final[int] = 409
HTTP_UNPROCESSABLE_ENTITY: Final[int] = 422
HTTP_TOO_MANY_REQUESTS: Final[int] = 429

# 服务器错误状态码
HTTP_INTERNAL_SERVER_ERROR: Final[int] = 500
HTTP_NOT_IMPLEMENTED: Final[int] = 501
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503

# ============================================================================
# 错误消息常量
# ============================================================================

# 通用错误消息
ERROR_INTERNAL_SERVER: Final[str] = "Internal server error"
ERROR_UNAUTHORIZED: Final[str] = "Unauthorized access"
ERROR_FORBIDDEN: Final[str] = "Access forbidden"
ERROR_NOT_FOUND: Final[str] = "Resource not found"
ERROR_METHOD_NOT_ALLOWED: Final[str] = "Method not allowed"
ERROR_VALIDATION_FAILED: Final[str] = "Validation failed"
ERROR_DATABASE_ERROR: Final[str] = "Database operation failed"

# 业务相关错误消息
ERROR_USER_NOT_FOUND: Final[str] = "User not found"
ERROR_USER_ALREADY_EXISTS: Final[str] = "User already exists"
ERROR_INVALID_CREDENTIALS: Final[str] = "Invalid credentials"
ERROR_INSUFFICIENT_PERMISSIONS: Final[str] = "Insufficient permissions"

# ============================================================================
# 数据库相关常量
# ============================================================================

# 数据库表名
TABLE_USER_VISITS: Final[str] = "t_user_visits"

# 字段长度限制
MAX_NAME_LENGTH: Final[int] = 100
MAX_EMAIL_LENGTH: Final[int] = 255
MAX_DESCRIPTION_LENGTH: Final[int] = 500

# 默认值
DEFAULT_VISIT_COUNT: Final[int] = 1
DEFAULT_PAGE_SIZE: Final[int] = 10
MAX_PAGE_SIZE: Final[int] = 100

# ============================================================================
# 验证规则常量
# ============================================================================

# 用户相关验证规则
USER_NAME_RULES: Final[list] = [
    {'type': 'required', 'field': 'name'},
    {'type': 'string', 'field': 'name', 'min_length': 1, 'max_length': MAX_NAME_LENGTH}
]

USER_EMAIL_RULES: Final[list] = [
    {'type': 'required', 'field': 'email'},
    {'type': 'email', 'field': 'email'},
    {'type': 'string', 'field': 'email', 'max_length': MAX_EMAIL_LENGTH}
]

# 分页相关验证规则
PAGINATION_RULES: Final[list] = [
    {'type': 'integer', 'field': 'page', 'min_value': 1},
    {'type': 'integer', 'field': 'per_page', 'min_value': 1, 'max_value': MAX_PAGE_SIZE}
]

# 搜索相关验证规则
SEARCH_RULES: Final[list] = [
    {'type': 'string', 'field': 'query', 'max_length': 200},
    {'type': 'string', 'field': 'sort_by', 'max_length': 50},
    {'type': 'string', 'field': 'sort_order', 'max_length': 10}
]

# ============================================================================
# 响应消息常量
# ============================================================================

# 成功消息
SUCCESS_CREATED: Final[str] = "Resource created successfully"
SUCCESS_UPDATED: Final[str] = "Resource updated successfully"
SUCCESS_DELETED: Final[str] = "Resource deleted successfully"
SUCCESS_OPERATION: Final[str] = "Operation completed successfully"

# ============================================================================
# 时间相关常量
# ============================================================================

# 时间格式
DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT: Final[str] = "%Y-%m-%d"
TIME_FORMAT: Final[str] = "%H:%M:%S"
ISO_DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S.%fZ"

# 缓存时间（秒）
CACHE_1_MINUTE: Final[int] = 60
CACHE_5_MINUTES: Final[int] = 300
CACHE_1_HOUR: Final[int] = 3600
CACHE_1_DAY: Final[int] = 86400

# ============================================================================
# 安全相关常量
# ============================================================================

# JWT 配置
JWT_ACCESS_TOKEN_EXPIRES: Final[int] = 3600  # 1小时
JWT_REFRESH_TOKEN_EXPIRES: Final[int] = 2592000  # 30天

# 密码策略
MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 128

# ============================================================================
# API 路由前缀常量
# ============================================================================

API_PREFIX: Final[str] = "/api"
API_V1_PREFIX: Final[str] = f"{API_PREFIX}/{API_VERSION}"

# ============================================================================
# 日志相关常量
# ============================================================================

# 日志级别
LOG_LEVEL_DEBUG: Final[str] = "DEBUG"
LOG_LEVEL_INFO: Final[str] = "INFO"
LOG_LEVEL_WARNING: Final[str] = "WARNING"
LOG_LEVEL_ERROR: Final[str] = "ERROR"
LOG_LEVEL_CRITICAL: Final[str] = "CRITICAL"

# 日志格式
LOG_FORMAT_SIMPLE: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_DETAILED: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"

# ============================================================================
# 导出常量
# ============================================================================

__all__ = [
    # 应用配置
    'APP_NAME', 'APP_VERSION', 'API_VERSION',
    'ENV_DEVELOPMENT', 'ENV_PRODUCTION', 'ENV_TESTING',
    'DEFAULT_DATABASE_URL', 'DEFAULT_JWT_SECRET_KEY', 'DEFAULT_PORT', 'DEFAULT_HOST',
    
    # HTTP 状态码
    'HTTP_OK', 'HTTP_CREATED', 'HTTP_ACCEPTED', 'HTTP_NO_CONTENT',
    'HTTP_BAD_REQUEST', 'HTTP_UNAUTHORIZED', 'HTTP_FORBIDDEN', 'HTTP_NOT_FOUND',
    'HTTP_METHOD_NOT_ALLOWED', 'HTTP_CONFLICT', 'HTTP_UNPROCESSABLE_ENTITY', 'HTTP_TOO_MANY_REQUESTS',
    'HTTP_INTERNAL_SERVER_ERROR', 'HTTP_NOT_IMPLEMENTED', 'HTTP_SERVICE_UNAVAILABLE',
    
    # 错误消息
    'ERROR_INTERNAL_SERVER', 'ERROR_UNAUTHORIZED', 'ERROR_FORBIDDEN', 'ERROR_NOT_FOUND',
    'ERROR_METHOD_NOT_ALLOWED', 'ERROR_VALIDATION_FAILED', 'ERROR_DATABASE_ERROR',
    'ERROR_USER_NOT_FOUND', 'ERROR_USER_ALREADY_EXISTS', 'ERROR_INVALID_CREDENTIALS', 'ERROR_INSUFFICIENT_PERMISSIONS',
    
    # 数据库相关
    'TABLE_USER_VISITS', 'MAX_NAME_LENGTH', 'MAX_EMAIL_LENGTH', 'MAX_DESCRIPTION_LENGTH',
    'DEFAULT_VISIT_COUNT', 'DEFAULT_PAGE_SIZE', 'MAX_PAGE_SIZE',
    
    # 验证规则
    'USER_NAME_RULES', 'USER_EMAIL_RULES', 'PAGINATION_RULES', 'SEARCH_RULES',
    
    # 响应消息
    'SUCCESS_CREATED', 'SUCCESS_UPDATED', 'SUCCESS_DELETED', 'SUCCESS_OPERATION',
    
    # 时间相关
    'DATETIME_FORMAT', 'DATE_FORMAT', 'TIME_FORMAT', 'ISO_DATETIME_FORMAT',
    'CACHE_1_MINUTE', 'CACHE_5_MINUTES', 'CACHE_1_HOUR', 'CACHE_1_DAY',
    
    # 安全相关
    'JWT_ACCESS_TOKEN_EXPIRES', 'JWT_REFRESH_TOKEN_EXPIRES',
    'MIN_PASSWORD_LENGTH', 'MAX_PASSWORD_LENGTH',
    
    # API 路由
    'API_PREFIX', 'API_V1_PREFIX',
    
    # 日志相关
    'LOG_LEVEL_DEBUG', 'LOG_LEVEL_INFO', 'LOG_LEVEL_WARNING', 'LOG_LEVEL_ERROR', 'LOG_LEVEL_CRITICAL',
    'LOG_FORMAT_SIMPLE', 'LOG_FORMAT_DETAILED',
]