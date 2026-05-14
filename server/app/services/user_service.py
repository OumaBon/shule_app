from app.schemas.user_schema import (user_schema, users_schema)
from app.models.user import User
from app import db 
from marshmallow import ValidationError 
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

class UserService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance._initialised = False  # Fixed: Changed _initilised to _initialised
        return cls._instance  
    
    def __init__(self):
        # Fixed: Check _initialised attribute
        if hasattr(self, '_initialised') and self._initialised:
            return 
       
        self.user_schema = user_schema
        self.users_schema = users_schema
        self._initialised = True  # Fixed: Changed _initilised to _initialised
    
    def create_user(self, data):
        try:
            # Fixed: Need to set password before saving
            user = self.user_schema.load(data, session=db.session)
            # Set password hash
            if 'password' in data:
                user.set_password(data['password'])
            db.session.add(user)
            db.session.commit()
            return self.user_schema.dump(user), None, 201
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            return None, {"error": "User with this email or username already exists."}, 400
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_users(self):
        try:
            users = User.query.all()
            return self.users_schema.dump(users), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
        
    def get_user(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, {"error": "User not found."}, 404
            return self.user_schema.dump(user), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500    
        
    def update_user(self, user_id, data):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, {"error": "User not found."}, 404
            
            # Fixed: Handle password update separately
            updated_user = self.user_schema.load(data, instance=user, session=db.session, partial=True)
            
            # Update password if provided
            if 'password' in data and data['password']:
                updated_user.set_password(data['password'])
            
            db.session.commit()
            return self.user_schema.dump(updated_user), None, 200
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            return None, {"error": "User with this email or username already exists."}, 400
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            return None, {"error": "An unexpected error occurred."}, 500    
    
    def delete_user(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return None, {"error": "User not found."}, 404
            
            db.session.delete(user)
            db.session.commit()
            return None, None, 204
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            return None, {"error": "An unexpected error occurred."}, 500    

user_services = UserService()