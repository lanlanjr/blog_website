from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.models.post import Post
from app.models.comment import Comment
from app.forms.post import PostForm
from app.forms.comment import CommentForm
from app.models.notification import Notification
from werkzeug.utils import secure_filename
import os
import uuid

posts = Blueprint('posts', __name__)

@posts.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    
    if request.method == 'POST':
        print("=" * 50)
        print("PROCESSING NEW POST SUBMISSION")
        print(f"Form data keys: {list(request.form.keys())}")
        print(f"Title: {request.form.get('title')}")
        
        # Get content and check if it exists
        content = request.form.get('content')
        content_exists = content is not None
        content_len = len(content) if content else 0
        content_preview = content[:100] if content and len(content) > 0 else 'Empty'
        
        print(f"Content exists: {content_exists}")
        print(f"Content length: {content_len}")
        print(f"Content preview: {content_preview}")
        print("=" * 50)
        
        # Get title and content directly from form data
        title = request.form.get('title')
        
        # Basic validation
        if not title or title.strip() == '':
            flash('Post title cannot be empty.', 'danger')
            form.content.data = content  # Preserve content
            return render_template('create_post.html', title='New Post', form=form, legend='New Post')
            
        if not content or content.strip() == '' or content.strip() == '<p><br></p>':
            # Print more detailed info about the content
            print("CONTENT VALIDATION FAILED:")
            print(f"Content is None: {content is None}")
            print(f"Content is empty string: {content == ''}")
            print(f"Content stripped is empty: {content.strip() == '' if content else 'N/A'}")
            print(f"Content is just a blank paragraph: {content.strip() == '<p><br></p>' if content else 'N/A'}")
            
            flash('Post content cannot be empty.', 'danger')
            form.title.data = title  # Preserve title
            return render_template('create_post.html', title='New Post', form=form, legend='New Post')
        
        try:
            # Create new post
            post = Post(title=title, content=content, author=current_user)
            db.session.add(post)
            db.session.commit()
            print(f"Successfully created post ID: {post.id}")
            flash('Your post has been created!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating post: {str(e)}")
            flash(f'Error creating post: {str(e)}', 'danger')
            # Preserve the form data in case of error
            form.title.data = title
            form.content.data = content
            return render_template('create_post.html', title='New Post', form=form, legend='New Post')
    
    # For GET request, render an empty form
    return render_template('create_post.html', title='New Post', form=form, legend='New Post', editing=False)

@posts.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # If post is hidden and user is not the author or admin, abort with 404
    if post.is_hidden and (not current_user.is_authenticated or 
                          (current_user != post.author and not current_user.is_admin())):
        abort(404)
    
    # Check if user is logged in, if not redirect to restricted page
    if not current_user.is_authenticated:
        # Pass the post title and ID to the restricted page
        return render_template('restricted_content.html', 
                              title=post.title, 
                              post_id=post.id,
                              post_preview=post.content[:150] + '...' if len(post.content) > 150 else post.content)
    
    # Always create new form instances with CSRF tokens
    comment_form = CommentForm()
    reply_form = CommentForm()
    
    # Handle POST request
    if request.method == 'POST':
        print(f"Post route form data: {request.form}")
        
        # Get form data
        content = request.form.get('content')
        parent_id = request.form.get('parent_id')
        
        print(f"Content from form: {content}")
        print(f"Parent ID from form: {parent_id}")
        
        # Validate content
        if not content or content.strip() == '' or content.strip() == '<p><br></p>':
            flash('Comment content cannot be empty.', 'danger')
            return redirect(url_for('posts.post', post_id=post.id))
        
        # Check if user's account is approved
        if not current_user.is_approved and not current_user.is_admin():
            flash('Your account is pending approval. You cannot comment until your account is approved.', 'warning')
            return redirect(url_for('posts.post', post_id=post.id))
            
        # Process the comment
        if parent_id:
            # This is a reply to another comment
            parent_comment = Comment.query.get_or_404(parent_id)
            comment = Comment(
                content=content,
                post=post,
                author=current_user,
                parent_id=parent_comment.id
            )
            db.session.add(comment)
            db.session.commit()
            
            # Create notification for reply
            Notification.create_reply_notification(parent_comment, comment, current_user)
            
            flash('Your reply has been posted.', 'success')
        else:
            # This is a new comment
            comment = Comment(
                content=content,
                post=post,
                author=current_user
            )
            db.session.add(comment)
            db.session.commit()
            
            # Create notification for comment
            Notification.create_comment_notification(post, comment, current_user)
            
            flash('Your comment has been posted.', 'success')
        
        return redirect(url_for('posts.post', post_id=post.id))
    
    # Get all top-level comments (those without parent_id)
    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Pass forms with CSRF tokens to the template
    return render_template('post.html', 
                          title=post.title, 
                          post=post, 
                          comment_form=comment_form, 
                          reply_form=reply_form, 
                          comments=comments)

@posts.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_to_comment(comment_id):
    """Handle reply to a comment at any level of nesting"""
    parent_comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get_or_404(parent_comment.post_id)
    
    # Check if user's account is approved
    if not current_user.is_approved and not current_user.is_admin():
        flash('Your account is pending approval. You cannot reply until your account is approved.', 'warning')
        return redirect(url_for('posts.post', post_id=post.id))
    
    form = CommentForm()
    
    # Debug print statements
    print(f"Reply form data: {request.form}")
    
    # Handle the content from Quill editor - it comes as form data, not automatically processed
    content = request.form.get('content')
    if not content or content.strip() == '' or content.strip() == '<p><br></p>':
        flash('Reply content cannot be empty.', 'danger')
        return redirect(url_for('posts.post', post_id=post.id))
    
    # Manually set form data to pass validation
    form.content.data = content
    form.parent_id.data = comment_id
    
    if form.validate():
        # Create a new reply
        reply = Comment(
            content=content,
            post=post,
            author=current_user,
            parent_id=comment_id
        )
        db.session.add(reply)
        db.session.commit()
        
        # Create notification for reply
        Notification.create_reply_notification(parent_comment, reply, current_user)
        
        flash('Your reply has been posted.', 'success')
    else:
        # If form validation fails, show errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    
    return redirect(url_for('posts.post', post_id=post.id))

@posts.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    # Get the post first, then check permissions
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin():
        abort(403)
        
    # Create a new form for this request
    form = PostForm()
    
    if request.method == 'POST':
        print("=" * 50)
        print(f"UPDATE POST FORM DATA:")
        print(f"Form keys: {list(request.form.keys())}")
        print(f"Title: {request.form.get('title')}")
        
        # Get content and check if it exists
        content = request.form.get('content')
        content_exists = content is not None
        content_len = len(content) if content else 0
        content_preview = content[:100] if content and len(content) > 0 else 'Empty'
        
        print(f"Content exists: {content_exists}")
        print(f"Content length: {content_len}")
        print(f"Content preview: {content_preview}")
        print("=" * 50)
        
        # Get title and content directly from form data
        title = request.form.get('title')
        
        # Basic validation
        if not title or title.strip() == '':
            flash('Post title cannot be empty.', 'danger')
            # Pass the existing content back to the form
            form.content.data = content
            return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')
            
        if not content or content.strip() == '' or content.strip() == '<p><br></p>':
            # Print more detailed info about the content
            print("CONTENT VALIDATION FAILED:")
            print(f"Content is None: {content is None}")
            print(f"Content is empty string: {content == ''}")
            print(f"Content stripped is empty: {content.strip() == '' if content else 'N/A'}")
            print(f"Content is just a blank paragraph: {content.strip() == '<p><br></p>' if content else 'N/A'}")
            
            flash('Post content cannot be empty.', 'danger')
            form.title.data = title
            return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')
            
        # Update post
        post.title = title
        post.content = content
        # Track who last modified the post
        post.last_modified_by_id = current_user.id
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
        
    elif request.method == 'GET':
        # For GET request, we'll use a direct approach instead of relying on WTForms
        # to ensure the content is properly passed to the template
                
        # Debug information
        print("=" * 50)
        print(f"LOADING POST FOR EDIT:")
        print(f"Post ID: {post.id}")
        print(f"Title: {post.title}")
        print(f"Content length: {len(post.content)}")
        print(f"Content preview: {post.content[:100]}...")
        print("=" * 50)
        
        # Display additional debug information about the content
        print(f"Content being passed to template: {len(post.content)}")
        
        # Explicitly set the form data
        form.title.data = post.title
        form.content.data = post.content
        
        # Directly pass the post data to the template context for maximum control
        return render_template(
            'create_post.html', 
            title='Update Post', 
            form=form, 
            legend='Update Post', 
            post_content=post.content,
            editing=True
        )
    
    # Normal rendering for other cases
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@posts.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    try:
        post = Post.query.get_or_404(post_id)
        if post.author != current_user and not current_user.is_admin():
            abort(403)
        
        # Get post details for confirmation message
        title = post.title
        
        # Delete the post
        db.session.delete(post)
        db.session.commit()
        
        flash(f'"{title}" has been deleted!', 'success')
        return redirect(url_for('main.home'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting post: {str(e)}', 'danger')
        return redirect(url_for('posts.post', post_id=post_id))

@posts.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    try:
        comment = Comment.query.get_or_404(comment_id)
        post_id = comment.post_id
        
        # Check if user is authorized to delete this comment
        if comment.author != current_user and not current_user.is_admin():
            abort(403)
        
        # Get comment type for message
        comment_type = "reply" if comment.get_depth() > 0 else "comment"
        
        # Delete the comment
        db.session.delete(comment)
        db.session.commit()
        
        flash(f'Your {comment_type} has been deleted!', 'success')
        return redirect(url_for('posts.post', post_id=post_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting comment: {str(e)}', 'danger')
        return redirect(url_for('posts.post', post_id=post_id))

@posts.route('/post/<int:post_id>/toggle_visibility', methods=['POST'])
@login_required
def toggle_visibility(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Only post author or admin can toggle visibility
    if post.author != current_user and not current_user.is_admin():
        abort(403)
    
    # Toggle visibility
    post.is_hidden = not post.is_hidden
    db.session.commit()
    
    status = "hidden" if post.is_hidden else "visible"
    flash(f'"{post.title}" is now {status}.', 'success')
    
    # Redirect back to post or to profile if post is hidden
    if post.is_hidden:
        return redirect(url_for('users.user_posts', username=post.author.username))
    else:
        return redirect(url_for('posts.post', post_id=post.id))

@posts.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    # Check for the correct file parameter based on Jodit/Froala requirements
    file_param = 'files[0]'  # Jodit default
    if file_param not in request.files:
        # Try other common parameters
        for param in ['image', 'file', 'files[]', 'upload']:
            if param in request.files:
                file_param = param
                break
        
        if file_param not in request.files:
            return jsonify({
                'error': 'No file part',
                'success': False,
                'message': 'No file uploaded'
            }), 400
    
    file = request.files[file_param]
    
    if file.filename == '':
        return jsonify({
            'error': 'No selected file',
            'success': False,
            'message': 'No file selected'
        }), 400
    
    if file and allowed_file(file.filename):
        # Securely generate a filename
        filename = secure_filename(file.filename)
        # Add a unique identifier to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(uploads_dir, unique_filename)
        file.save(file_path)
        
        # Create a URL for the image
        image_url = url_for('static', filename=f'uploads/{unique_filename}')
        
        # Return in format compatible with multiple editors
        return jsonify({
            'success': True,
            'files': [image_url],  # Jodit expects 'files' array
            'link': image_url,     # Froala expects 'link'
            'url': image_url,      # Others might expect 'url'
            'name': unique_filename,
            'message': 'Upload successful'
        })
    
    return jsonify({
        'error': 'File type not allowed',
        'success': False,
        'message': 'File type not allowed'
    }), 400

def allowed_file(filename):
    # Define allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 