import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    DB_SERVER = os.getenv('DB_SERVER')
    DB_NAME = os.getenv('DB_NAME')
    DB_USERNAME = os.getenv('DB_USERNAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    

    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    

    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_STORAGE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'exam-media')
    
 
    HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', 300))

    EXAM_AUTO_SUBMIT_BUFFER = int(os.getenv('EXAM_AUTO_SUBMIT_BUFFER', 30))
    EXAM_ARCHIVE_DAYS = int(os.getenv('EXAM_ARCHIVE_DAYS', 30))