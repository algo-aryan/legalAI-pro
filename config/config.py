# config/config.py - Configuration settings

import os

class Config:
    """Configuration settings for LegalAI Pro"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    
    # Google API settings
    GOOGLE_API_KEY_CONTRACT = os.environ.get('GOOGLE_API_KEY_CONTRACT') or 'AIzaSyDlTDhMX73MNJTiXV67hfeCdWzCFqE_aGg'
    GOOGLE_API_KEY_GENERAL = os.environ.get('GOOGLE_API_KEY_GENERAL') or 'AIzaSyB3kerSj-u1oSxzKx5QGjNy3Xp_TZ9EX9E'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'uploads'
    VECTORSTORE_FOLDER = 'vectorstore'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']
    
    # Model settings
    CONTRACT_MODEL = "gemini-2.5-flash"
    GENERAL_MODEL = "gemini-2.5-pro"
    EMBEDDING_MODEL = "models/embedding-001"
    TEMPERATURE = 0.3
    
    # Development settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize app configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}