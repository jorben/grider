"""
验证模块测试
符合项目规范的测试文件
"""
import pytest
from flask import Flask, request
import json

from app.utils.validation import (
    validate_required, validate_string, validate_integer, validate_enum, validate_email,
    validate_all, validate_with_rules, validate_json, validate_query,
    validate_form, validate_combined, VALIDATION_RULES
)


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    return app


class TestValidationFunctions:
    """验证函数测试类"""

    def test_validate_required_success(self):
        """测试必填字段验证成功"""
        data = {'name': 'John', 'email': 'john@example.com'}
        result = validate_required(data, ['name', 'email'])
        assert result is None

    def test_validate_required_failure(self):
        """测试必填字段验证失败"""
        data = {'name': 'John'}
        result = validate_required(data, ['name', 'email'])
        assert result is not None
        assert result[1] == 400
        assert 'email' in result[0]['missing_fields']

    def test_validate_string_success(self):
        """测试字符串验证成功"""
        data = {'name': 'John Doe'}
        result = validate_string(data, 'name', min_length=1, max_length=100)
        assert result is None

    def test_validate_string_failure(self):
        """测试字符串验证失败"""
        data = {'name': ''}
        result = validate_string(data, 'name', min_length=1, max_length=100)
        assert result is not None
        assert result[1] == 400

    def test_validate_integer_success(self):
        """测试整数验证成功"""
        data = {'age': 25}
        result = validate_integer(data, 'age', min_value=18, max_value=100)
        assert result is None

    def test_validate_integer_failure(self):
        """测试整数验证失败"""
        data = {'age': 150}
        result = validate_integer(data, 'age', min_value=18, max_value=100)
        assert result is not None
        assert result[1] == 400

    def test_validate_email_success(self):
        """测试邮箱验证成功"""
        data = {'email': 'test@example.com'}
        result = validate_email(data, 'email')
        assert result is None

    def test_validate_email_failure(self):
        """测试邮箱验证失败"""
        data = {'email': 'invalid-email'}
        result = validate_email(data, 'email')
        assert result is not None
        assert result[1] == 400

    def test_validate_enum_success(self):
        """测试枚举验证成功"""
        data = {'status': 'active'}
        result = validate_enum(data, 'status', ['active', 'inactive', 'pending'])
        assert result is None

    def test_validate_enum_failure(self):
        """测试枚举验证失败"""
        data = {'status': 'unknown'}
        result = validate_enum(data, 'status', ['active', 'inactive', 'pending'])
        assert result is not None
        assert result[1] == 400
        assert 'must be one of' in result[0]['error']

    def test_validate_all_success(self):
        """测试批量验证成功"""
        data = {'name': 'John', 'age': 25, 'email': 'john@example.com', 'status': 'active'}
        rules = [
            {'type': 'required', 'field': 'name'},
            {'type': 'string', 'field': 'name', 'min_length': 1, 'max_length': 100},
            {'type': 'integer', 'field': 'age', 'min_value': 18, 'max_value': 100},
            {'type': 'email', 'field': 'email'},
            {'type': 'enum', 'field': 'status', 'enum_values': ['active', 'inactive', 'pending']}
        ]
        result = validate_all(data, rules)
        assert result is None

    def test_validate_with_rules_success(self):
        """测试预定义规则集验证成功"""
        data = {'name': 'Alice'}
        result = validate_with_rules(data, 'user_name')
        assert result is None


class TestValidationDecorators:
    """验证装饰器测试类"""

    def test_validate_json_decorator_success(self, app):
        """测试JSON验证装饰器成功"""
        with app.test_request_context('/test', method='POST',
                                     data=json.dumps({'name': 'John'}),
                                     content_type='application/json'):
            
            @validate_json([{'type': 'required', 'field': 'name'}])
            def test_route(validated_data):
                return validated_data
            
            result = test_route()
            assert result['name'] == 'John'

    def test_validate_json_decorator_failure(self, app):
        """测试JSON验证装饰器失败"""
        with app.test_request_context('/test', method='POST',
                                     data=json.dumps({}),
                                     content_type='application/json'):
            
            @validate_json([{'type': 'required', 'field': 'name'}])
            def test_route(validated_data):
                return validated_data
            
            result = test_route()
            assert isinstance(result, tuple)
            assert result[1] == 400

    def test_validate_query_decorator_success(self, app):
        """测试查询参数验证装饰器成功"""
        with app.test_request_context('/test?page=2&per_page=20', method='GET'):
            
            @validate_query([
                {'type': 'integer', 'field': 'page', 'min_value': 1},
                {'type': 'integer', 'field': 'per_page', 'min_value': 1, 'max_value': 100}
            ])
            def test_route(validated_data):
                return validated_data
            
            result = test_route()
            assert result['page'] == '2'
            assert result['per_page'] == '20'

    def test_validate_form_decorator_success(self, app):
        """测试表单验证装饰器成功"""
        with app.test_request_context('/test', method='POST',
                                     data={'name': 'Alice'},
                                     content_type='application/x-www-form-urlencoded'):
            
            @validate_form([{'type': 'required', 'field': 'name'}])
            def test_route(validated_data):
                return validated_data
            
            result = test_route()
            assert result['name'] == 'Alice'

    def test_validate_combined_decorator_success(self, app):
        """测试组合验证装饰器成功"""
        with app.test_request_context('/test?page=1', method='POST',
                                     data=json.dumps({'name': 'Bob'}),
                                     content_type='application/json'):
            
            @validate_combined([
                {'type': 'required', 'field': 'name'},
                {'type': 'integer', 'field': 'page', 'min_value': 1}
            ])
            def test_route(validated_data):
                return validated_data
            
            result = test_route()
            assert result['name'] == 'Bob'
            assert result['page'] == '1'


class TestValidationRules:
    """预定义规则集测试类"""

    def test_user_name_rules_success(self):
        """测试用户名称规则集成功"""
        data = {'name': 'Valid User'}
        result = validate_with_rules(data, 'user_name')
        assert result is None

    def test_user_name_rules_failure(self):
        """测试用户名称规则集失败"""
        data = {'name': ''}  # 空字符串
        result = validate_with_rules(data, 'user_name')
        assert result is not None

    def test_pagination_rules_success(self):
        """测试分页规则集成功"""
        data = {'page': 2, 'per_page': 20}
        result = validate_with_rules(data, 'pagination')
        assert result is None

    def test_pagination_rules_failure(self):
        """测试分页规则集失败"""
        data = {'page': 0, 'per_page': 200}  # 超出范围
        result = validate_with_rules(data, 'pagination')
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__])