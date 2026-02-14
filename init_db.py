"""
Database initialization script
Run this script once to create all database tables
"""

from app import app
from models import db

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("✓ Database tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - api_keys")
        print("  - chat_messages")
        print("  - pdf_documents")
        print("\nYou can now run the application with: python app.py")

if __name__ == '__main__':
    init_database()
