from datetime import datetime
from app import db

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_hidden = db.Column(db.Boolean, default=False)
    
    # Define the relationships explicitly with foreign_keys to avoid ambiguity
    author = db.relationship('User', foreign_keys=[user_id], backref='posts', lazy=True)
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id], lazy=True)
    
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.title}>' 