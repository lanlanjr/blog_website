from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models.user import User
from app.models.post import Post
from functools import wraps
from app.forms.admin import SystemNotificationForm
from app.models.notification import Notification, NotificationCategory

admin = Blueprint('admin', __name__)

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    posts = Post.query.all()
    pending_users = User.query.filter_by(is_approved=False).all()
    return render_template('admin/dashboard.html', title='Admin Dashboard', 
                          users=users, posts=posts, pending_users=pending_users)

@admin.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', title='Manage Users', users=users)

@admin.route('/admin/posts')
@login_required
@admin_required
def manage_posts():
    posts = Post.query.all()
    return render_template('admin/posts.html', title='Manage Posts', posts=posts)

@admin.route('/admin/pending_users')
@login_required
@admin_required
def pending_users():
    pending_users = User.query.filter_by(is_approved=False).all()
    return render_template('admin/pending_users.html', title='Pending Users', users=pending_users)

@admin.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.username} has been approved!', 'success')
    return redirect(url_for('admin.pending_users'))

@admin.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete your own admin account!', 'danger')
    else:
        # Delete all posts by the user
        Post.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/user/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot change your own role!', 'danger')
    else:
        user.role = 'admin' if user.role == 'user' else 'user'
        db.session.commit()
        flash(f'User {user.username} is now {user.role}!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/system-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def create_system_notification():
    form = SystemNotificationForm()
    
    if form.validate_on_submit():
        # Get all users or filter as needed
        if form.all_users.data:
            users = User.query.filter_by(is_approved=True).all()
        else:
            # In future, could add user selection logic here
            users = User.query.filter_by(is_approved=True).all()
        
        # Get title and customize the notification
        title = form.title.data
        message = form.message.data
        link = form.link.data if form.link.data else None
        
        # Create the system notification
        notification_count = len(users)
        Notification.create_system_notification(users, message, link, title)
        
        flash(f'System notification sent to {notification_count} users.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('admin/create_notification.html', title='Send System Notification', form=form)

@admin.route('/admin/system-notifications', methods=['GET'])
@login_required
@admin_required
def view_system_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get all system notifications
    system_category = NotificationCategory.query.filter_by(name="System").first()
    if not system_category:
        return render_template('admin/system_notifications.html', title='System Notifications History', 
                              notifications=None, grouped_notifications=[])
    
    # Get all system notifications by creation time (newest first)
    all_notifications = Notification.query.filter_by(
        category_id=system_category.id,
        notification_type=Notification.TYPE_SYSTEM
    ).order_by(Notification.created_at.desc()).all()
    
    # Group notifications by content (title, message, link)
    grouped_notifications = []
    notification_groups = {}
    
    for notification in all_notifications:
        # Create a key that identifies unique notifications
        key = f"{notification.title}|{notification.message}|{notification.link or 'None'}"
        
        if key in notification_groups:
            # Add this notification to existing group
            notification_groups[key]['count'] += 1
            notification_groups[key]['instances'].append(notification)
            # Update the timestamp if this one is newer
            if notification.created_at > notification_groups[key]['latest_timestamp']:
                notification_groups[key]['latest_timestamp'] = notification.created_at
        else:
            # Create a new group
            notification_groups[key] = {
                'notification': notification,
                'count': 1,
                'instances': [notification],
                'latest_timestamp': notification.created_at
            }
    
    # Convert the grouped dictionary to a list sorted by latest timestamp
    for key, group in notification_groups.items():
        grouped_notifications.append({
            'notification': group['notification'],
            'count': group['count'],
            'latest_timestamp': group['latest_timestamp']
        })
    
    # Sort by the latest timestamp (newest first)
    grouped_notifications.sort(key=lambda x: x['latest_timestamp'], reverse=True)
    
    # Manual pagination since we're grouping after the query
    total_items = len(grouped_notifications)
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1  # Ceiling division
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    current_page_items = grouped_notifications[start_idx:end_idx] if total_items > 0 else []
    
    # Create a pagination object with iter_pages method
    class CustomPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page if total > 0 else 1
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
        
        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge or
                    (num > self.page - left_current - 1 and num < self.page + right_current) or
                    num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    pagination = CustomPagination(
        items=current_page_items,
        page=page,
        per_page=per_page,
        total=total_items
    )
    
    return render_template('admin/system_notifications.html', title='System Notifications History', 
                          notifications=None, grouped_notifications=current_page_items, 
                          pagination=pagination) 