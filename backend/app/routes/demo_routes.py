from flask import Blueprint, request, jsonify
from app.services.user_service import get_or_create_user_visit, get_all_user_visits
from app.utils.validation import (
    validate_json, validate_query, validate_form, validate_all
)
from app.constants import (
    USER_NAME_RULES, PAGINATION_RULES, SEARCH_RULES,
    HTTP_OK, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR,
    ERROR_INTERNAL_SERVER
)

bp = Blueprint('demo_routes', __name__)

# 示例1: 使用装饰器验证JSON请求体（POST请求）
@bp.route('/hello', methods=['POST'])
@validate_json(USER_NAME_RULES)
def say_hello(validated_data):
    """
    Say hello接口 - 使用装饰器验证JSON请求体
    接收name字段，返回问候语和访问时间信息
    """
    name = validated_data['name'].strip()
    
    try:
        # 使用服务层处理业务逻辑
        result = get_or_create_user_visit(name)
        user_visit = result['user_visit']
        previous_visit = result['previous_visit']
        current_visit = result['current_visit']
        
        # 构建响应数据
        response_data = {
            'message': f'Hi, {user_visit.name}',
            'current_visit': current_visit.isoformat()
        }
        
        if previous_visit:
            response_data['previous_visit'] = previous_visit.isoformat()
        else:
            response_data['previous_visit'] = 'This is your first visit!'
        
        return jsonify(response_data), HTTP_OK
        
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTP_BAD_REQUEST
    except Exception as e:
        return jsonify({'error': ERROR_INTERNAL_SERVER}), HTTP_INTERNAL_SERVER_ERROR

# 示例2: 使用装饰器验证查询参数（GET请求）
@bp.route('/visits', methods=['GET'])
@validate_query(PAGINATION_RULES)
def get_all_visits(validated_data):
    """
    获取所有用户访问记录 - 使用装饰器验证查询参数
    """
    try:
        # 从验证后的数据获取参数
        page = int(validated_data.get('page', 1))
        per_page = int(validated_data.get('per_page', 10))
        
        # 获取所有访问记录
        visits = get_all_user_visits()
        
        # 简单的内存分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_visits = visits[start_idx:end_idx]
        
        return jsonify({
            'data': [visit.to_dict() for visit in paginated_visits],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(visits),
                'pages': (len(visits) + per_page - 1) // per_page
            }
        }), HTTP_OK
        
    except Exception as e:
        return jsonify({'error': ERROR_INTERNAL_SERVER}), HTTP_INTERNAL_SERVER_ERROR

# 示例3: 使用组合验证（同时验证查询参数和搜索参数）
@bp.route('/search', methods=['GET'])
@validate_query(PAGINATION_RULES + SEARCH_RULES)
def search_visits(validated_data):
    """
    搜索用户访问记录 - 验证多个查询参数
    """
    try:
        # 从验证后的数据获取参数
        page = int(validated_data.get('page', 1))
        per_page = int(validated_data.get('per_page', 10))
        query = validated_data.get('query')
        sort_by = validated_data.get('sort_by')
        sort_order = validated_data.get('sort_order', 'asc')
        
        # 获取所有访问记录
        visits = get_all_user_visits()
        
        # 搜索过滤
        if query:
            visits = [visit for visit in visits if query.lower() in visit.name.lower()]
        
        # 排序
        if sort_by and hasattr(visits[0] if visits else None, sort_by):
            reverse = sort_order == 'desc'
            visits.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)
        
        # 分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_visits = visits[start_idx:end_idx]
        
        return jsonify({
            'data': [visit.to_dict() for visit in paginated_visits],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(visits),
                'pages': (len(visits) + per_page - 1) // per_page
            },
            'search': {
                'query': query,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }), HTTP_OK
        
    except Exception as e:
        return jsonify({'error': ERROR_INTERNAL_SERVER}), HTTP_INTERNAL_SERVER_ERROR

# 示例4: 手动验证（保持原有方式，用于对比）
@bp.route('/manual', methods=['POST'])
def manual_validation():
    """
    手动验证示例 - 保持原有验证方式
    """
    data = request.get_json() or {}
    
    # 手动调用验证函数
    result = validate_all(data, USER_NAME_RULES)
    if result:
        return jsonify(result[0]), result[1]
    
    name = data['name'].strip()
    
    try:
        result = get_or_create_user_visit(name)
        return jsonify({
            'message': f'Hi, {result["user_visit"].name}',
            'current_visit': result['current_visit'].isoformat()
        }), HTTP_OK
        
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTP_BAD_REQUEST
    except Exception as e:
        return jsonify({'error': ERROR_INTERNAL_SERVER}), HTTP_INTERNAL_SERVER_ERROR

# 示例5: 表单数据验证（POST请求，表单数据）
@bp.route('/form', methods=['POST'])
@validate_form(USER_NAME_RULES)
def form_validation(validated_data):
    """
    表单数据验证示例 - 处理表单提交
    """
    name = validated_data['name'].strip()
    
    try:
        result = get_or_create_user_visit(name)
        return jsonify({
            'message': f'Form submitted for {result["user_visit"].name}',
            'current_visit': result['current_visit'].isoformat()
        }), HTTP_OK
        
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTP_BAD_REQUEST
    except Exception as e:
        return jsonify({'error': ERROR_INTERNAL_SERVER}), HTTP_INTERNAL_SERVER_ERROR