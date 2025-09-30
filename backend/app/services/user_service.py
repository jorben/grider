from datetime import datetime
from typing import Optional, Dict, Any
from app import db
from app.models.user import UserVisit

def get_or_create_user_visit(name: str) -> Dict[str, Any]:
    """
    获取或创建用户访问记录
    返回包含用户信息和访问时间的字典
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    
    name = name.strip()
    user_visit = UserVisit.query.filter_by(name=name).first()
    previous_visit = None
    
    if user_visit:
        previous_visit = user_visit.last_visit
        user_visit.last_visit = datetime.utcnow()
    else:
        user_visit = UserVisit(name=name, last_visit=datetime.utcnow())
        db.session.add(user_visit)
    
    db.session.commit()
    
    return {
        'user_visit': user_visit,
        'previous_visit': previous_visit,
        'current_visit': datetime.utcnow()
    }

def get_user_visit_by_name(name: str) -> Optional[UserVisit]:
    """根据名称获取用户访问记录"""
    return UserVisit.query.filter_by(name=name).first()

def get_all_user_visits() -> list[UserVisit]:
    """获取所有用户访问记录"""
    return UserVisit.query.all()

def create_user_visit(name: str) -> UserVisit:
    """创建新的用户访问记录"""
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    
    name = name.strip()
    
    # 检查是否已存在
    existing_user = get_user_visit_by_name(name)
    if existing_user:
        raise ValueError(f"User with name '{name}' already exists")
    
    user_visit = UserVisit(name=name, last_visit=datetime.utcnow())
    db.session.add(user_visit)
    db.session.commit()
    
    return user_visit

def update_user_visit_time(name: str) -> UserVisit:
    """更新用户访问时间"""
    user_visit = get_user_visit_by_name(name)
    if not user_visit:
        raise ValueError(f"User with name '{name}' not found")
    
    user_visit.last_visit = datetime.utcnow()
    db.session.commit()
    
    return user_visit