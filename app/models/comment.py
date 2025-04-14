from datetime import datetime
from app import db

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='comments')
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Helper method to get all replies (nested)
    def get_all_replies(self):
        """Recursively get all replies to this comment"""
        all_replies = list(self.replies)
        for reply in self.replies:
            all_replies.extend(reply.get_all_replies())
        return all_replies
    
    # Helper method to get reply depth
    def get_depth(self):
        """Get the nesting depth of this comment"""
        if not self.parent_id:
            return 0
        depth = 1
        parent = self.parent
        while parent.parent_id:
            depth += 1
            parent = parent.parent
        return depth
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.author.username}>' 