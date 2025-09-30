"""
Pytest configuration for Flask application tests
"""

import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a CLI runner for the Flask app"""
    return app.test_cli_runner()