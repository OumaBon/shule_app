from app.schemas.user_schema import (user_schema, users_schema)
from app.models.user import User



class UserService:
    @staticmethod
    def create_user(data):
        user = user_schema.load(data)
        user.set_password(data['password'])
        user.save()
        return user_schema.dump(user)

    @staticmethod
    def get_user_by_id(user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        return user_schema.dump(user)

    @staticmethod
    def get_all_users():
        users = User.query.all()
        return users_schema.dump(users)

    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return None
        
        for key, value in data.items():
            setattr(user, key, value)
        
        if 'password' in data:
            user.set_password(data['password'])
        
        user.save()
        return user_schema.dump(user)

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False
        
        user.delete()
        return True