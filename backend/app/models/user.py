from datetime import datetime
from app import db
from app.constants import TABLE_USER_VISITS, MAX_NAME_LENGTH, DEFAULT_VISIT_COUNT

class UserVisit(db.Model):
    __tablename__ = TABLE_USER_VISITS
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False, unique=True)
    last_visit = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visit_count = db.Column(db.Integer, nullable=False, default=DEFAULT_VISIT_COUNT)
    
    def __repr__(self):
        return f'<UserVisit {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'last_visit': self.last_visit.isoformat(),
            'created_at': self.created_at.isoformat(),
            'visit_count': self.visit_count
        }