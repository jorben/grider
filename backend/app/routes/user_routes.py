from flask import Blueprint, request, jsonify
from app.services.user_service import get_or_create_user_visit, get_all_user_visits

bp = Blueprint('user_routes', __name__)

@bp.route('/hello', methods=['POST'])
def say_hello():
    """
    Say hello接口
    接收name字段，返回问候语和访问时间信息
    """
    data = request.get_json()
    
    # 输入验证
    if not data or 'name' not in data:
        return jsonify({'error': 'Name field is required'}), 400
    
    name = data['name']
    if not name or not name.strip():
        return jsonify({'error': 'Name cannot be empty'}), 400
    
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
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/visits', methods=['GET'])
def get_all_visits():
    """
    获取所有用户访问记录
    """
    try:
        visits = get_all_user_visits()
        return jsonify([visit.to_dict() for visit in visits]), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500