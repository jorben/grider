"""
常量模块测试
验证常量模块的功能和正确性
"""

import pytest
from app.constants import (
    # 应用配置常量
    APP_NAME, APP_VERSION, API_VERSION,
    ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING,
    DEFAULT_DATABASE_URL, DEFAULT_JWT_SECRET_KEY, DEFAULT_PORT, DEFAULT_HOST,
    
    # HTTP 状态码常量
    HTTP_OK, HTTP_CREATED, HTTP_ACCEPTED, HTTP_NO_CONTENT,
    HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED, HTTP_FORBIDDEN, HTTP_NOT_FOUND,
    HTTP_METHOD_NOT_ALLOWED, HTTP_CONFLICT, HTTP_UNPROCESSABLE_ENTITY, HTTP_TOO_MANY_REQUESTS,
    HTTP_INTERNAL_SERVER_ERROR, HTTP_NOT_IMPLEMENTED, HTTP_SERVICE_UNAVAILABLE,
    
    # 错误消息常量
    ERROR_INTERNAL_SERVER, ERROR_UNAUTHORIZED, ERROR_FORBIDDEN, ERROR_NOT_FOUND,
    ERROR_METHOD_NOT_ALLOWED, ERROR_VALIDATION_FAILED, ERROR_DATABASE_ERROR,
    ERROR_USER_NOT_FOUND, ERROR_USER_ALREADY_EXISTS, ERROR_INVALID_CREDENTIALS, ERROR_INSUFFICIENT_PERMISSIONS,
    
    # 数据库相关常量
    TABLE_USER_VISITS, MAX_NAME_LENGTH, MAX_EMAIL_LENGTH, MAX_DESCRIPTION_LENGTH,
    DEFAULT_VISIT_COUNT, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
    
    # 验证规则常量
    USER_NAME_RULES, USER_EMAIL_RULES, PAGINATION_RULES, SEARCH_RULES,
    
    # 响应消息常量
    SUCCESS_CREATED, SUCCESS_UPDATED, SUCCESS_DELETED, SUCCESS_OPERATION,
    
    # 时间相关常量
    DATETIME_FORMAT, DATE_FORMAT, TIME_FORMAT, ISO_DATETIME_FORMAT,
    CACHE_1_MINUTE, CACHE_5_MINUTES, CACHE_1_HOUR, CACHE_1_DAY,
    
    # 安全相关常量
    JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES,
    MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    
    # API 路由前缀常量
    API_PREFIX, API_V1_PREFIX,
    
    # 日志相关常量
    LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR, LOG_LEVEL_CRITICAL,
    LOG_FORMAT_SIMPLE, LOG_FORMAT_DETAILED,
)


class TestConstants:
    """常量模块测试类"""
    
    def test_app_config_constants(self):
        """测试应用配置常量"""
        assert APP_NAME == "Grider Backend"
        assert APP_VERSION == "1.0.0"
        assert API_VERSION == "v1"
        
        assert ENV_DEVELOPMENT == "development"
        assert ENV_PRODUCTION == "production"
        assert ENV_TESTING == "testing"
        
        assert DEFAULT_DATABASE_URL == "sqlite:///app.db"
        assert DEFAULT_JWT_SECRET_KEY == "your-secret-key-change-in-production"
        assert DEFAULT_PORT == 5000
        assert DEFAULT_HOST == "127.0.0.1"
    
    def test_http_status_constants(self):
        """测试HTTP状态码常量"""
        # 成功状态码
        assert HTTP_OK == 200
        assert HTTP_CREATED == 201
        assert HTTP_ACCEPTED == 202
        assert HTTP_NO_CONTENT == 204
        
        # 客户端错误状态码
        assert HTTP_BAD_REQUEST == 400
        assert HTTP_UNAUTHORIZED == 401
        assert HTTP_FORBIDDEN == 403
        assert HTTP_NOT_FOUND == 404
        assert HTTP_METHOD_NOT_ALLOWED == 405
        assert HTTP_CONFLICT == 409
        assert HTTP_UNPROCESSABLE_ENTITY == 422
        assert HTTP_TOO_MANY_REQUESTS == 429
        
        # 服务器错误状态码
        assert HTTP_INTERNAL_SERVER_ERROR == 500
        assert HTTP_NOT_IMPLEMENTED == 501
        assert HTTP_SERVICE_UNAVAILABLE == 503
    
    def test_error_message_constants(self):
        """测试错误消息常量"""
        assert ERROR_INTERNAL_SERVER == "Internal server error"
        assert ERROR_UNAUTHORIZED == "Unauthorized access"
        assert ERROR_FORBIDDEN == "Access forbidden"
        assert ERROR_NOT_FOUND == "Resource not found"
        assert ERROR_METHOD_NOT_ALLOWED == "Method not allowed"
        assert ERROR_VALIDATION_FAILED == "Validation failed"
        assert ERROR_DATABASE_ERROR == "Database operation failed"
        
        assert ERROR_USER_NOT_FOUND == "User not found"
        assert ERROR_USER_ALREADY_EXISTS == "User already exists"
        assert ERROR_INVALID_CREDENTIALS == "Invalid credentials"
        assert ERROR_INSUFFICIENT_PERMISSIONS == "Insufficient permissions"
    
    def test_database_constants(self):
        """测试数据库相关常量"""
        assert TABLE_USER_VISITS == "t_user_visits"
        assert MAX_NAME_LENGTH == 100
        assert MAX_EMAIL_LENGTH == 255
        assert MAX_DESCRIPTION_LENGTH == 500
        
        assert DEFAULT_VISIT_COUNT == 1
        assert DEFAULT_PAGE_SIZE == 10
        assert MAX_PAGE_SIZE == 100
    
    def test_validation_rules_constants(self):
        """测试验证规则常量"""
        # 用户名称验证规则
        assert len(USER_NAME_RULES) == 2
        assert USER_NAME_RULES[0]['type'] == 'required'
        assert USER_NAME_RULES[0]['field'] == 'name'
        assert USER_NAME_RULES[1]['type'] == 'string'
        assert USER_NAME_RULES[1]['field'] == 'name'
        
        # 分页验证规则
        assert len(PAGINATION_RULES) == 2
        assert PAGINATION_RULES[0]['type'] == 'integer'
        assert PAGINATION_RULES[0]['field'] == 'page'
        assert PAGINATION_RULES[1]['type'] == 'integer'
        assert PAGINATION_RULES[1]['field'] == 'per_page'
    
    def test_success_message_constants(self):
        """测试成功消息常量"""
        assert SUCCESS_CREATED == "Resource created successfully"
        assert SUCCESS_UPDATED == "Resource updated successfully"
        assert SUCCESS_DELETED == "Resource deleted successfully"
        assert SUCCESS_OPERATION == "Operation completed successfully"
    
    def test_time_constants(self):
        """测试时间相关常量"""
        assert DATETIME_FORMAT == "%Y-%m-%d %H:%M:%S"
        assert DATE_FORMAT == "%Y-%m-%d"
        assert TIME_FORMAT == "%H:%M:%S"
        assert ISO_DATETIME_FORMAT == "%Y-%m-%dT%H:%M:%S.%fZ"
        
        assert CACHE_1_MINUTE == 60
        assert CACHE_5_MINUTES == 300
        assert CACHE_1_HOUR == 3600
        assert CACHE_1_DAY == 86400
    
    def test_security_constants(self):
        """测试安全相关常量"""
        assert JWT_ACCESS_TOKEN_EXPIRES == 3600  # 1小时
        assert JWT_REFRESH_TOKEN_EXPIRES == 2592000  # 30天
        
        assert MIN_PASSWORD_LENGTH == 8
        assert MAX_PASSWORD_LENGTH == 128
    
    def test_api_constants(self):
        """测试API相关常量"""
        assert API_PREFIX == "/api"
        assert API_V1_PREFIX == "/api/v1"
    
    def test_logging_constants(self):
        """测试日志相关常量"""
        assert LOG_LEVEL_DEBUG == "DEBUG"
        assert LOG_LEVEL_INFO == "INFO"
        assert LOG_LEVEL_WARNING == "WARNING"
        assert LOG_LEVEL_ERROR == "ERROR"
        assert LOG_LEVEL_CRITICAL == "CRITICAL"
        
        assert "%(asctime)s" in LOG_FORMAT_SIMPLE
        assert "%(asctime)s" in LOG_FORMAT_DETAILED
        assert "%(module)s" in LOG_FORMAT_DETAILED


def test_constants_are_final():
    """测试常量是否被正确标记为Final类型"""
    # 这个测试验证常量是否被正确导入和使用
    # 在实际使用中，这些常量应该被当作不可变的值
    assert isinstance(APP_NAME, str)
    assert isinstance(HTTP_OK, int)
    assert isinstance(MAX_NAME_LENGTH, int)
    assert isinstance(USER_NAME_RULES, list)


if __name__ == "__main__":
    pytest.main([__file__])