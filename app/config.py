import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # MySQL database configuration
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    
    # Construct SQLAlchemy URI with proper formatting for ngrok
    SQLALCHEMY_DATABASE_URI = f'mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enhanced connection pool settings for ngrok
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,  # Reduced pool size for better stability
        'pool_recycle': 1800,  # Recycle connections every 30 minutes
        'pool_pre_ping': True,  # Enable connection health checks
        'pool_timeout': 30,  # Connection timeout in seconds
        'max_overflow': 2,  # Maximum number of connections that can be created beyond pool_size
        'connect_args': {
            'connect_timeout': 30,
            'read_timeout': 30,
            'write_timeout': 30,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'ssl': {
                'verify_cert': False  # Disable SSL verification for ngrok
            }
        }
    }
    
    # Print connection info (without password) for debugging
    print(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB} as {MYSQL_USER}")