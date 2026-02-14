from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()
bcrypt = Bcrypt()

# Generate or use a fixed encryption key for API keys
# In production, store this securely in environment variables
def get_encryption_key():
    """Get or generate encryption key, ensuring it's bytes"""
    key = os.getenv('ENCRYPTION_KEY')
    if key:
        # If key is provided, ensure it's bytes
        return key.encode() if isinstance(key, str) else key
    else:
        # Generate a new key and print warning
        new_key = Fernet.generate_key()
        print("\n" + "="*70)
        print("⚠️  WARNING: No ENCRYPTION_KEY found in .env file!")
        print("="*70)
        print("A temporary encryption key has been generated for this session.")
        print("Add this to your .env file to persist encrypted API keys:")
        print(f"\nENCRYPTION_KEY={new_key.decode()}\n")
        print("Without this, you'll need to re-add your API keys on restart.")
        print("="*70 + "\n")
        return new_key

ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    pdf_documents = db.relationship('PDFDocument', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class APIKey(db.Model):
    """API Key model for storing Groq API keys"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_value_encrypted = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_key_value(self, key_value):
        """Encrypt and store the API key"""
        self.key_value_encrypted = cipher_suite.encrypt(key_value.encode()).decode()
    
    def get_key_value(self):
        """Decrypt and return the API key"""
        return cipher_suite.decrypt(self.key_value_encrypted.encode()).decode()
    
    def get_masked_key(self):
        """Return a masked version of the API key for display"""
        try:
            key = self.get_key_value()
            if len(key) > 8:
                return f"{key[:4]}...{key[-4:]}"
            return "****"
        except:
            return "****"
    
    def __repr__(self):
        return f'<APIKey {self.label}>'


class ChatMessage(db.Model):
    """Chat message model for storing conversation history"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), default='English')
    pdf_name = db.Column(db.String(255), nullable=True)  # Name of PDF if context-based
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.role} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'language': self.language,
            'pdf_name': self.pdf_name,
            'timestamp': self.timestamp.isoformat()
        }


class PDFDocument(db.Model):
    """PDF Document model for storing uploaded PDFs with vector embeddings"""
    __tablename__ = 'pdf_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    page_count = db.Column(db.Integer, nullable=True)
    text_content = db.Column(db.Text, nullable=False)  # Extracted text
    vector_store_data = db.Column(db.LargeBinary, nullable=True)  # Serialized FAISS index
    is_active = db.Column(db.Boolean, default=True)  # Currently selected PDF
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PDFDocument {self.filename}>'
    
    def to_dict(self):
        """Convert PDF to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'page_count': self.page_count,
            'is_active': self.is_active,
            'uploaded_at': self.uploaded_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat()
        }
