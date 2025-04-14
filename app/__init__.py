from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from app.config import Config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create static directory if it doesn't exist
    if not os.path.exists(os.path.join(app.root_path, 'static')):
        os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
        
    # Create profile pictures directory if it doesn't exist
    os.makedirs(os.path.join(app.root_path, 'static/profile_pics'), exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    # Context processors
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf())

    # Register blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.post import posts
    from app.routes.admin import admin
    from app.routes.user import users
    from app.routes.notification_routes import notifications
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(posts)
    app.register_blueprint(admin)
    app.register_blueprint(users)
    app.register_blueprint(notifications)

    # Create error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

# Import this at the bottom to avoid circular imports
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment 