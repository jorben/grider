"""
常量模块
集中管理应用中的所有常量，便于维护和统一管理
"""

from typing import Final

APP_VERSION: str = "1.2.4"

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

# 网格策略分析验证规则 ['etfCode', 'totalCapital', 'gridType', 'riskPreference', 'adjustmentCoefficient']
GRID_ANALYZE_RULES: Final[list] = [
    {'type': 'required', 'field': 'etfCode'},
    {'type': 'required', 'field': 'totalCapital'},
    {'type': 'required', 'field': 'gridType'},
    {'type': 'required', 'field': 'riskPreference'},
    {'type': 'integer', 'field': 'totalCapital', 'min_value': 10000, 'max_value': 1000000},
    {'type': 'enum', 'field': 'gridType', 'enum_values': ['等比', '等差']},
    {'type': 'enum', 'field': 'riskPreference', 'enum_values': ['低频', '均衡', '高频']},
    {'type': 'float', 'field': 'adjustmentCoefficient', 'min_value': 0, 'max_value': 2}
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
# 业务相关常量
# ============================================================================
# 热门ETF列表
ETF_POPULAR_LIST: Final[list] = [
    {'code': '510300', 'name': '沪深300ETF'},
    {'code': '510500', 'name': '中证500ETF'},
    {'code': '159919', 'name': '沪深300ETF'},
    {'code': '159915', 'name': '创业板ETF'},
    {'code': '512880', 'name': '证券ETF'},
    {'code': '515050', 'name': '5G通信ETF'},
    {'code': '512690', 'name': '酒ETF'},
    {'code': '516160', 'name': '新能源ETF'},
    {'code': '159928', 'name': '消费ETF'},
    {'code': '512170', 'name': '医疗ETF'},
    {'code': '159941', 'name': '纳指ETF'},
    {'code': '513100', 'name': '纳指ETF'},
    {'code': '159920', 'name': '恒生ETF'},
    {'code': '510880', 'name': '红利ETF'},
    {'code': '588000', 'name': '科创50ETF'},
    {'code': '512480', 'name': '半导体ETF'},
    {'code': '159819', 'name': '人工智能ETF'},
    {'code': '159742', 'name': '恒生科技ETF'},
    {'code': '159949', 'name': '创业板50ETF'},
    {'code': '3032', 'name': '恒生科技ETF'},
    {'code': 'SPY', 'name': 'S&P500ETF'}
]

# 常用资金
CAPITAL_PRESETS: Final[list] = [
    {'value': 100000, 'label': '10万', 'popular': True},
    {'value': 200000, 'label': '20万', 'popular': True},
    {'value': 300000, 'label': '30万', 'popular': False},
    {'value': 500000, 'label': '50万', 'popular': True},
    {'value': 800000, 'label': '80万', 'popular': False},
    {'value': 1000000, 'label': '100万', 'popular': True},
    {'value': 1500000, 'label': '150万', 'popular': False},
    {'value': 2000000, 'label': '200万', 'popular': False}
]

# ============================================================================
# 导出常量
# ============================================================================

__all__ = [

    'APP_VERSION',
    
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
    'USER_NAME_RULES', 'USER_EMAIL_RULES', 'PAGINATION_RULES', 'SEARCH_RULES', 'GRID_ANALYZE_RULES',
    
    # 响应消息
    'SUCCESS_CREATED', 'SUCCESS_UPDATED', 'SUCCESS_DELETED', 'SUCCESS_OPERATION',
    
    # 时间相关
    'DATETIME_FORMAT', 'DATE_FORMAT', 'TIME_FORMAT', 'ISO_DATETIME_FORMAT',
    'CACHE_1_MINUTE', 'CACHE_5_MINUTES', 'CACHE_1_HOUR', 'CACHE_1_DAY',
    
    # 安全相关
    'JWT_ACCESS_TOKEN_EXPIRES', 'JWT_REFRESH_TOKEN_EXPIRES',
    'MIN_PASSWORD_LENGTH', 'MAX_PASSWORD_LENGTH',

    # 业务相关
    'ETF_POPULAR_LIST', 'CAPITAL_PRESETS',
    
]