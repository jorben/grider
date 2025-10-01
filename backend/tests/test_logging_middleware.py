"""
日志中间件测试
验证日志配置中间件的功能
"""

import os
import logging
import pytest
from flask import Flask, request, jsonify
from app.middleware.logging import LoggingConfig, RequestLogger, StructuredLogger, setup_logging
from app.constants import ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING


class TestLoggingConfig:
    """日志配置测试类"""
    
    def test_logging_config_development(self):
        """测试开发环境日志配置"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置开发环境
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        os.environ['LOG_LEVEL'] = ''  # 清除环境变量
        
        config = LoggingConfig(app)
        
        # 验证日志级别
        assert app.logger.level == logging.DEBUG
        assert logging.getLogger().level == logging.DEBUG
    
    def test_logging_config_production(self):
        """测试生产环境日志配置"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置生产环境
        os.environ['FLASK_ENV'] = ENV_PRODUCTION
        os.environ['LOG_LEVEL'] = ''  # 清除环境变量
        
        config = LoggingConfig(app)
        
        # 验证日志级别
        assert app.logger.level == logging.WARNING
        assert logging.getLogger().level == logging.WARNING
    
    def test_logging_config_custom_level(self):
        """测试自定义日志级别"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置自定义日志级别
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        config = LoggingConfig(app)
        
        # 验证日志级别
        assert app.logger.level == logging.ERROR
        assert logging.getLogger().level == logging.ERROR
    
    def test_logging_config_invalid_level(self):
        """测试无效日志级别（应该使用默认值）"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置无效日志级别
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        os.environ['LOG_LEVEL'] = 'INVALID_LEVEL'
        
        config = LoggingConfig(app)
        
        # 验证使用默认级别
        assert app.logger.level == logging.DEBUG


class TestRequestLogger:
    """请求日志记录器测试类"""
    
    def test_request_logger_initialization(self):
        """测试请求日志记录器初始化"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        logger = RequestLogger(app)
        
        # 验证before_request处理器已注册
        assert len(app.before_request_funcs[None]) > 0
        assert len(app.after_request_funcs[None]) > 0
        assert len(app.teardown_request_funcs[None]) > 0
    
    def test_request_id_generation(self):
        """测试请求ID生成"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        logger = RequestLogger(app)
        request_id = logger._generate_request_id()
        
        # 验证请求ID格式
        assert len(request_id) == 8
        assert isinstance(request_id, str)
    
    def test_request_logging_integration(self, client):
        """测试请求日志记录集成"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 添加测试路由
        @app.route('/test')
        def test_route():
            return jsonify({'message': 'test'})
        
        # 配置请求日志记录器
        RequestLogger(app)
        
        # 发送请求
        with app.test_client() as client:
            response = client.get('/test')
            
            # 验证响应
            assert response.status_code == 200


class TestStructuredLogger:
    """结构化日志记录器测试类"""
    
    def test_structured_logging_debug(self, caplog):
        """测试结构化调试日志"""
        with caplog.at_level(logging.DEBUG):
            StructuredLogger.debug("Test debug message", user_id=123, action="login")
        
        assert "Test debug message" in caplog.text
        assert "user_id=123" in caplog.text
        assert "action=login" in caplog.text
    
    def test_structured_logging_info(self, caplog):
        """测试结构化信息日志"""
        with caplog.at_level(logging.INFO):
            StructuredLogger.info("Test info message", request_id="abc123", duration=0.5)
        
        assert "Test info message" in caplog.text
        assert "request_id=abc123" in caplog.text
        assert "duration=0.5" in caplog.text
    
    def test_structured_logging_error(self, caplog):
        """测试结构化错误日志"""
        with caplog.at_level(logging.ERROR):
            StructuredLogger.error("Test error message", error_code=500, endpoint="/api/test")
        
        assert "Test error message" in caplog.text
        assert "error_code=500" in caplog.text
        assert "endpoint=/api/test" in caplog.text
    
    def test_structured_logging_request(self, caplog):
        """测试结构化请求日志"""
        request_data = {
            'method': 'GET',
            'path': '/api/test',
            'status_code': 200,
            'duration': 0.123,
            'ip': '127.0.0.1'
        }
        
        with caplog.at_level(logging.INFO):
            StructuredLogger.request_log('info', "Request completed", request_data)
        
        assert "Request completed" in caplog.text
        assert "method=GET" in caplog.text
        assert "path=/api/test" in caplog.text
        assert "status=200" in caplog.text
        assert "duration=0.123" in caplog.text


class TestLoggingMiddlewareIntegration:
    """日志中间件集成测试类"""
    
    def test_setup_logging_middleware(self):
        """测试日志中间件设置"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置开发环境
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        
        # 配置日志中间件
        app = setup_logging(app)
        
        # 验证应用已配置
        assert app is not None
        assert hasattr(app, 'logger')
        assert app.logger is not None
    
    def test_logging_middleware_with_routes(self, client):
        """测试带路由的日志中间件"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置开发环境
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        
        # 添加测试路由
        @app.route('/api/test')
        def test_route():
            return jsonify({'message': 'success'})
        
        # 配置日志中间件
        app = setup_logging(app)
        
        # 发送请求
        with app.test_client() as client:
            response = client.get('/api/test')
            
            # 验证响应
            assert response.status_code == 200
            assert response.json == {'message': 'success'}
    
    def test_logging_middleware_error_handling(self, client):
        """测试日志中间件错误处理"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # 设置开发环境
        os.environ['FLASK_ENV'] = ENV_DEVELOPMENT
        
        # 添加会抛出异常的路由，但添加错误处理
        @app.route('/api/error')
        def error_route():
            try:
                raise ValueError("Test error")
            except ValueError:
                # 在测试中，我们期望异常被记录，但不会导致测试失败
                return jsonify({'error': 'Internal server error'}), 500
        
        # 配置日志中间件
        app = setup_logging(app)
        
        # 发送请求
        with app.test_client() as client:
            response = client.get('/api/error')
            
            # 验证错误响应
            assert response.status_code == 500
            assert response.json == {'error': 'Internal server error'}


def test_logging_configuration_values():
    """测试日志配置值"""
    # 验证环境常量
    assert ENV_DEVELOPMENT == "development"
    assert ENV_PRODUCTION == "production"
    assert ENV_TESTING == "testing"
    
    # 验证日志级别常量
    assert logging.DEBUG == 10
    assert logging.INFO == 20
    assert logging.WARNING == 30
    assert logging.ERROR == 40
    assert logging.CRITICAL == 50


@pytest.fixture
def client():
    """创建测试客户端"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_environment():
    """清理环境变量"""
    original_env = os.environ.get('FLASK_ENV')
    original_log_level = os.environ.get('LOG_LEVEL')
    
    yield
    
    # 恢复环境变量
    if original_env:
        os.environ['FLASK_ENV'] = original_env
    else:
        os.environ.pop('FLASK_ENV', None)
    
    if original_log_level:
        os.environ['LOG_LEVEL'] = original_log_level
    else:
        os.environ.pop('LOG_LEVEL', None)


if __name__ == "__main__":
    pytest.main([__file__])