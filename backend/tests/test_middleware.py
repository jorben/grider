"""
Middleware module tests
"""

import pytest
from app.middleware.registry import get_registered_middlewares, clear_middleware_registry
from app.middleware.cors import get_cors_config


class TestMiddlewareRegistry:
    """Test middleware registry functionality"""
    
    def test_get_registered_middlewares(self):
        """Test getting registered middlewares"""
        middlewares = get_registered_middlewares()
        assert isinstance(middlewares, list)
        assert 'setup_cors' in middlewares
    
    def test_clear_middleware_registry(self):
        """Test clearing middleware registry"""
        # Store original count
        original_count = len(get_registered_middlewares())
        
        # Clear registry
        clear_middleware_registry()
        
        # Check it's empty
        assert len(get_registered_middlewares()) == 0
        
        # Re-register CORS middleware (restore state)
        from app.middleware.registry import _middleware_registry
        from app.middleware.cors import setup_cors
        _middleware_registry.append(setup_cors)
        
        # Verify restoration
        assert len(get_registered_middlewares()) == original_count


class TestCorsMiddleware:
    """Test CORS middleware functionality"""
    
    def test_cors_config_defaults(self):
        """Test CORS configuration defaults"""
        config = get_cors_config()
        
        assert config['origins'] == '*'
        assert config['methods'] == 'GET,POST,PUT,DELETE,OPTIONS'
        assert config['headers'] == 'Content-Type,Authorization'
        assert config['supports_credentials'] is False
    
    def test_cors_middleware_integration(self, client):
        """Test CORS middleware integration with Flask app"""
        # Test OPTIONS request (preflight)
        response = client.options('/api/user/hello')
        assert response.status_code == 200
        
        # Check CORS headers
        headers = dict(response.headers)
        assert 'Access-Control-Allow-Origin' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Expose-Headers' in headers
        # Note: Access-Control-Allow-Methods may not be present in simple CORS responses
    
    def test_cors_headers_on_get_request(self, client):
        """Test CORS headers on GET request"""
        response = client.get('/api/user/visits')
        assert response.status_code == 200
        
        # Check CORS headers
        headers = dict(response.headers)
        assert 'Access-Control-Allow-Origin' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'
    
    def test_cors_preflight_with_origin_header(self, client):
        """Test CORS preflight with Origin header"""
        response = client.options(
            '/api/user/hello',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        assert response.status_code == 200
        
        # Check CORS headers
        headers = dict(response.headers)
        # Flask-CORS may echo back the origin when specific origin is provided
        assert 'Access-Control-Allow-Origin' in headers
        # Allow either '*' or the specific origin
        allowed_origin = headers['Access-Control-Allow-Origin']
        assert allowed_origin in ['*', 'http://localhost:3000']
        # Check for CORS headers presence
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers


class TestMiddlewareErrorHandling:
    """Test middleware error handling"""
    
    def test_middleware_registry_with_invalid_function(self):
        """Test middleware registry with invalid function"""
        from app.middleware.registry import register_middleware
        
        # This should not raise an exception
        def invalid_middleware():
            return "not a flask app"
        
        # Register should work, but application might fail later
        register_middleware(invalid_middleware)
        
        # Clean up
        clear_middleware_registry()
        from app.middleware.registry import _middleware_registry
        from app.middleware.cors import setup_cors
        _middleware_registry.append(setup_cors)