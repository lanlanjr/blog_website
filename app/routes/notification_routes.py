from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationCategory, NotificationStatus, NotificationSettings
from app import db, csrf

notifications = Blueprint('notifications', __name__)

@notifications.route('/notifications', methods=['GET'])
@login_required
def view_all():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    category = request.args.get('category')
    status = request.args.get('status')
    time_period = request.args.get('time_period')
    
    # Base query
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if category and category != 'all':
        query = query.filter_by(category_id=category)
    
    if status:
        if status == 'read':
            query = query.filter_by(status=NotificationStatus.READ)
        elif status == 'unread':
            query = query.filter_by(status=NotificationStatus.UNREAD)
    
    if time_period:
        now = datetime.now()
        if time_period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Notification.created_at >= start_date)
        elif time_period == 'week':
            start_date = now - timedelta(days=7)
            query = query.filter(Notification.created_at >= start_date)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
            query = query.filter(Notification.created_at >= start_date)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Notification.created_at.desc())
    
    # Pagination
    notifications = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get all notification categories for filter dropdown
    categories = NotificationCategory.query.all()
    
    # Count unread notifications
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, 
        status=NotificationStatus.UNREAD
    ).count()
    
    return render_template(
        'notifications.html',
        notifications=notifications,
        categories=categories,
        unread_count=unread_count,
        selected_category=category,
        selected_status=status,
        selected_time_period=time_period
    )

@notifications.route('/notifications/unread', methods=['GET'])
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        status=NotificationStatus.UNREAD
    ).count()
    return jsonify({'count': count})

@notifications.route('/notifications/latest', methods=['GET'])
@login_required
def get_latest():
    """Get the latest 5 unread notifications for the current user"""
    limit = request.args.get('limit', 5, type=int)
    
    # Get the latest unread notifications
    latest_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        status=NotificationStatus.UNREAD
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    # Convert to dictionaries
    notifications = []
    for notification in latest_notifications:
        notification_dict = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'category': notification.category.name if notification.category else None,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'link': notification.link
        }
        notifications.append(notification_dict)
    
    return jsonify({
        'notifications': notifications
    })

@notifications.route('/notifications/latest_id', methods=['GET'])
@login_required
def get_latest_id():
    """Get the ID of the latest notification for the current user"""
    latest_notification = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.id.desc()).first()
    
    latest_id = latest_notification.id if latest_notification else 0
    
    return jsonify({
        'latest_id': latest_id
    })

@notifications.route('/notifications/<int:notification_id>', methods=['GET'])
@login_required
def view_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Mark as read if unread
    if notification.status == NotificationStatus.UNREAD:
        notification.mark_as_read()
    
    # If notification has a link, redirect to it
    if notification.link:
        return redirect(notification.link)
    
    # Otherwise render notification detail page
    return render_template(
        'notification_detail.html',
        notification=notification
    )

@notifications.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Get user's notification settings or create if not exists
    user_settings = NotificationSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = NotificationSettings.create_default_settings(current_user)
    
    # Get all notification categories
    categories = NotificationCategory.query.all()
    
    if request.method == 'POST':
        # Check if any settings were actually changed
        changes_made = False
        
        # Check email settings changes
        email_enabled = 'email_enabled' in request.form
        email_digest = 'email_digest' in request.form
        if user_settings.email_enabled != email_enabled or user_settings.email_digest != email_digest:
            user_settings.email_enabled = email_enabled
            user_settings.email_digest = email_digest
            changes_made = True
        
        # Check push notification changes
        push_enabled = 'push_enabled' in request.form
        if user_settings.push_enabled != push_enabled:
            user_settings.push_enabled = push_enabled
            changes_made = True
        
        # Check category subscription changes
        new_category_ids = set(request.form.getlist('category_ids', type=int))
        current_category_ids = {category.id for category in user_settings.subscribed_categories}
        
        if new_category_ids != current_category_ids:
            user_settings.update_subscriptions(list(new_category_ids))
            changes_made = True
        
        # Only save and show message if changes were made
        if changes_made:
            db.session.commit()
            flash('Notification settings updated successfully', 'success')
        
        return redirect(url_for('notifications.settings'))
    
    return render_template(
        'notification_settings.html',
        settings=user_settings,
        categories=categories
    )

@notifications.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
@csrf.exempt
def mark_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    else:
        return redirect(url_for('notifications.view_all'))

@notifications.route('/notifications/mark_all_read', methods=['POST'])
@login_required
@csrf.exempt
def mark_all_read():
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        status=NotificationStatus.UNREAD
    ).all()
    
    for notification in unread_notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'count': 0})
    else:
        flash('All notifications marked as read', 'success')
        return redirect(url_for('notifications.view_all'))

@notifications.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    else:
        # Only flash message if not redirecting to notifications page
        referrer = request.referrer
        if referrer and not '/notifications' in referrer:
            flash('Notification deleted', 'success')
        return redirect(url_for('notifications.view_all'))

@notifications.route('/notifications/clear_all', methods=['POST'])
@login_required
@csrf.exempt
def clear_all():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    else:
        # Only flash if not already on notifications page
        referrer = request.referrer
        if referrer and not '/notifications' in referrer:
            flash('All notifications cleared', 'success')
        return redirect(url_for('notifications.view_all'))

@notifications.route('/notifications/fix_categories', methods=['POST'])
@login_required
def fix_notification_categories():
    # Only admin users can run this
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('notifications.view_all'))
    
    # Fix missing notification categories
    updated_count = Notification.fix_missing_categories()
    
    flash(f'Fixed {updated_count} notifications with missing categories.', 'success')
    return redirect(url_for('notifications.view_all')) 