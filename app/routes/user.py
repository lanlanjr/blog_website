import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models.user import User
from app.models.post import Post
from app.forms.user import UpdateProfileForm, ChangePasswordForm

users = Blueprint('users', __name__)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    
    # Resize image to save space
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    
    image_file = url_for('static', filename='profile_pics/' + current_user.profile_picture)
    return render_template('user/profile.html', title='Profile', 
                           image_file=image_file, form=form)

@users.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('users.profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    return render_template('user/change_password.html', title='Change Password', form=form)

@users.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    
    # If the current user is the profile owner or an admin, show all posts
    if current_user.is_authenticated and (current_user.id == user.id or current_user.is_admin()):
        posts_query = Post.query.filter_by(author=user)
    # Otherwise, hide hidden posts
    else:
        posts_query = Post.query.filter_by(author=user, is_hidden=False)
    
    posts = posts_query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    
    return render_template('user/user_posts.html', posts=posts, user=user) 