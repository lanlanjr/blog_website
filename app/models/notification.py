from datetime import datetime
from app import db
from enum import Enum

# Define notification status
class NotificationStatus(Enum):
    UNREAD = 'unread'
    READ = 'read'

class NotificationCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))  # Font awesome icon name
    
    # Notifications in this category
    notifications = db.relationship('Notification', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<NotificationCategory {self.name}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('notification_category.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    
    # Notification types
    TYPE_COMMENT = 'comment'             # Someone commented on your post
    TYPE_REPLY = 'reply'                 # Someone replied to your comment
    TYPE_MENTION = 'mention'             # Someone mentioned you in a post or comment
    TYPE_POST_UPDATE = 'post_update'     # Post you follow was updated
    TYPE_LIKE = 'like'                   # Someone liked your post or comment
    TYPE_SYSTEM = 'system'               # System notification (announcements, etc.)
    TYPE_USER_APPROVAL = 'user_approval' # Account approved by admin
    
    notification_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)  # Optional link to relevant page
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    created_at = db.Column(db.DateTime, default=datetime.now)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications_received', foreign_keys=[user_id])
    sender = db.relationship('User', backref='notifications_sent', foreign_keys=[sender_id])
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title[:20]}...>'
    
    def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category.name if self.category else None,
            'type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def create_comment_notification(cls, post, comment, sender):
        """Create a notification when someone comments on a post"""
        # Don't notify if the commenter is the post author
        if post.author.id == sender.id:
            return None
        
        # Get Comments category
        comments_category = NotificationCategory.query.filter_by(name="Comments").first()
            
        notification = cls(
            user_id=post.author.id,
            sender_id=sender.id,
            post_id=post.id,
            comment_id=comment.id,
            category_id=comments_category.id if comments_category else None,
            notification_type=cls.TYPE_COMMENT,
            title="New Comment",
            message=f"{sender.username} commented on your post '{post.title}'",
            link=f"/post/{post.id}#comment-{comment.id}",
            status=NotificationStatus.UNREAD
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @classmethod
    def create_reply_notification(cls, comment, reply, sender):
        """Create a notification when someone replies to a comment"""
        # Don't notify if the replier is the comment author
        if comment.author.id == sender.id:
            return None
        
        # Get Replies category
        replies_category = NotificationCategory.query.filter_by(name="Replies").first()
            
        notification = cls(
            user_id=comment.author.id,
            sender_id=sender.id,
            post_id=comment.post_id,
            comment_id=reply.id,
            category_id=replies_category.id if replies_category else None,
            notification_type=cls.TYPE_REPLY,
            title="New Reply",
            message=f"{sender.username} replied to your comment",
            link=f"/post/{comment.post_id}#comment-{reply.id}",
            status=NotificationStatus.UNREAD
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @classmethod
    def create_system_notification(cls, users, message, link=None, title="System Notification"):
        """Create a system notification for multiple users"""
        # Get System category
        system_category = NotificationCategory.query.filter_by(name="System").first()
        
        notifications = []
        for user in users:
            notification = cls(
                user_id=user.id,
                category_id=system_category.id if system_category else None,
                notification_type=cls.TYPE_SYSTEM,
                title=title,
                message=message,
                link=link,
                status=NotificationStatus.UNREAD
            )
            db.session.add(notification)
            notifications.append(notification)
        db.session.commit()
        return notifications
    
    @classmethod
    def create_approval_notification(cls, user):
        """Create a notification when a user's account is approved"""
        # Get System category
        system_category = NotificationCategory.query.filter_by(name="System").first()
        
        notification = cls(
            user_id=user.id,
            category_id=system_category.id if system_category else None,
            notification_type=cls.TYPE_USER_APPROVAL,
            title="Account Approved",
            message="Your account has been approved! You can now create posts and comments.",
            link="/profile",
            status=NotificationStatus.UNREAD
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def fix_missing_categories(cls):
        """Fix notifications with missing categories"""
        # Get all categories
        comment_category = NotificationCategory.query.filter_by(name="Comments").first()
        reply_category = NotificationCategory.query.filter_by(name="Replies").first()
        mention_category = NotificationCategory.query.filter_by(name="Mentions").first()
        system_category = NotificationCategory.query.filter_by(name="System").first()
        
        # Get notifications with missing categories
        notifications = cls.query.filter_by(category_id=None).all()
        
        updated_count = 0
        for notification in notifications:
            # Assign appropriate category based on notification type
            if notification.notification_type == cls.TYPE_COMMENT and comment_category:
                notification.category_id = comment_category.id
                updated_count += 1
            elif notification.notification_type == cls.TYPE_REPLY and reply_category:
                notification.category_id = reply_category.id
                updated_count += 1
            elif notification.notification_type == cls.TYPE_MENTION and mention_category:
                notification.category_id = mention_category.id
                updated_count += 1
            elif (notification.notification_type in [cls.TYPE_SYSTEM, cls.TYPE_USER_APPROVAL] 
                  and system_category):
                notification.category_id = system_category.id
                updated_count += 1
        
        # Save changes if any
        if updated_count > 0:
            db.session.commit()
            
        return updated_count

class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Email notification settings
    email_enabled = db.Column(db.Boolean, default=True)
    email_digest = db.Column(db.Boolean, default=False)  # True for daily digest, False for immediate
    
    # In-app notification settings
    push_enabled = db.Column(db.Boolean, default=True)
    
    # Relationship to user
    user = db.relationship('User', backref='notification_settings', uselist=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<NotificationSettings for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_enabled': self.email_enabled,
            'email_digest': self.email_digest,
            'push_enabled': self.push_enabled,
            'subscribed_categories': [category.name for category in self.subscribed_categories],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_default_settings(cls, user):
        """Create default notification settings for a new user"""
        settings = cls(
            user_id=user.id,
            email_enabled=True,
            email_digest=False,
            push_enabled=True
        )
        
        # Add default categories if they exist
        try:
            default_categories = NotificationCategory.query.all()
            if default_categories:
                settings.subscribed_categories = default_categories
        except:
            # Handle case where categories don't exist yet
            pass
            
        db.session.add(settings)
        db.session.commit()
        return settings
    
    def update_subscriptions(self, category_ids):
        """Update user's subscribed categories based on provided category IDs"""
        self.subscribed_categories = []
        if category_ids:
            categories = NotificationCategory.query.filter(NotificationCategory.id.in_(category_ids)).all()
            self.subscribed_categories = categories
        db.session.commit()
        return self.subscribed_categories
    
    def is_subscribed_to(self, category_id):
        """Check if user is subscribed to a specific category"""
        return any(category.id == category_id for category in self.subscribed_categories)

# Association table for users' subscribed categories
notification_categories = db.Table('notification_categories',
    db.Column('settings_id', db.Integer, db.ForeignKey('notification_settings.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('notification_category.id'), primary_key=True)
)

# Add the relationship after the association table is defined
NotificationSettings.subscribed_categories = db.relationship('NotificationCategory', 
                                                          secondary=notification_categories,
                                                          lazy='subquery',
                                                          backref=db.backref('subscribers', lazy=True)) 