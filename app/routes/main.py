from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.models.post import Post
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    # For non-admin users, filter out hidden posts that aren't their own
    if current_user.is_authenticated and not current_user.is_admin():
        posts = Post.query.filter(
            or_(
                Post.is_hidden == False,
                Post.user_id == current_user.id
            )
        ).order_by(Post.created_at.desc()).all()
    # For admin users, show all posts
    elif current_user.is_authenticated and current_user.is_admin():
        posts = Post.query.order_by(Post.created_at.desc()).all()
    # For non-authenticated users, only show non-hidden posts
    else:
        posts = Post.query.filter_by(is_hidden=False).order_by(Post.created_at.desc()).all()
    
    # If user is not logged in, show a limited homepage with previews
    if not current_user.is_authenticated:
        return render_template('restricted_home.html', posts=posts)
        
    return render_template('home.html', posts=posts)

@main.route('/about')
def about():
    return render_template('about.html', title='About') 