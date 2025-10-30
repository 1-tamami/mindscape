import os
import ast
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    # Core settings
    SECRET_KEY = os.getenv("FLASK_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI", "sqlite:///memochou.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Question categories and levels
    try:
        DEPTH = ast.literal_eval(os.getenv("DEPTH", "['surface', 'deep', 'core']"))
        CATEGORY = ast.literal_eval(os.getenv("CATEGORY", "['life', 'career', 'relationship', 'personal']"))
        STAGE = ast.literal_eval(os.getenv("STAGE", "['past', 'present', 'future']"))
    except (ValueError, TypeError):
        DEPTH = ['surface', 'deep', 'core']
        CATEGORY = ['life', 'career', 'relationship', 'personal']
        STAGE = ['past', 'present', 'future']
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MIN_PASSWORD_LENGTH_CHANGE = 10
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # File upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
