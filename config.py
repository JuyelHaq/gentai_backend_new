import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
    BASE_UPLOAD_FOLDER = os.getenv('BASE_UPLOAD_FOLDER')

    SECRET_KEY = os.getenv('SECRET_KEY')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_DATABASE'),
    }
    MASTER_DATABASE = os.getenv('MASTER_DATABASE')
