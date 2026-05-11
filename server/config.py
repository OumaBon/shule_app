import os 
from dotenv import load_dotenv 
load_dotenv()



Base_Dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or "something_secretandvertygedgt"
    DEBUG = True
    UPLOAD_FOLDER = os.path.join(Base_Dir, 'static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 86400  # 24 hours   
    JWT_LOCATIONS = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    @staticmethod
    def init_app(app):
        pass      


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(Base_Dir, 'dev-data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False 


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_TEST_DATABASE_URI') or \
        'sqlite:///' + os.path.join(Base_Dir, 'test-data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig}
     