import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # Fix for Railway PostgreSQL URL compatibility
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Check if using Railway internal hostname (only works within Railway network)
    if 'railway.internal' in database_url:
        print("\n" + "="*70)
        print("⚠️  WARNING: Railway Internal Database URL Detected")
        print("="*70)
        print("You're using a Railway internal hostname that only works within")
        print("Railway's network. For local development, you need the PUBLIC URL.")
        print("\nHow to fix:")
        print("1. Go to your Railway project dashboard")
        print("2. Click on your PostgreSQL service")
        print("3. Go to the 'Connect' tab")
        print("4. Copy the 'Public Networking' URL (NOT the private URL)")
        print("5. Update DATABASE_URL in your .env file")
        print("\nOR use SQLite for local development:")
        print("DATABASE_URL=sqlite:///app.db")
        print("\n🔄 Falling back to SQLite for now...")
        print("="*70 + "\n")
        database_url = 'sqlite:///app.db'
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Conditional engine options (SQLite doesn't support pooling)
    if database_url.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    # Upload configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
