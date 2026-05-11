from .base_repository import BaseRepository
from app.models.user import User
from app import db
from typing import Optional, List, Dict, Any
from sqlalchemy import or_, and_

class UserRepository(BaseRepository):
    """Repository for User model with specific queries"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.model.query.filter_by(email=email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.model.query.filter_by(username=username).first()
    
    def get_by_role(self, role: str, is_active: bool = True) -> List[User]:
        """Get users by role"""
        return self.model.query.filter_by(role=role, is_active=is_active).all()
    
    def get_active_users_by_role(self, role: str) -> List[User]:
        """Get active users by role"""
        return self.model.query.filter_by(role=role, is_active=True).all()
    
    def get_users_by_name(self, first_name: str = None, last_name: str = None) -> List[User]:
        """Search users by name"""
        query = self.model.query
        if first_name:
            query = query.filter(self.model.first_name.ilike(f'%{first_name}%'))
        if last_name:
            query = query.filter(self.model.last_name.ilike(f'%{last_name}%'))
        return query.all()
    
    def search_users(self, search_term: str) -> List[User]:
        """Search users across multiple fields"""
        return self.model.query.filter(
            or_(
                self.model.first_name.ilike(f'%{search_term}%'),
                self.model.last_name.ilike(f'%{search_term}%'),
                self.model.email.ilike(f'%{search_term}%'),
                self.model.username.ilike(f'%{search_term}%'),
                self.model.phone.ilike(f'%{search_term}%')
            )
        ).all()
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        """Update user's last login timestamp"""
        user = self.get_by_id(user_id)
        if user:
            user.last_login = db.func.now()
            db.session.commit()
            return user
        return None
    
    def get_teachers_list(self) -> List[User]:
        """Get all teachers with their profiles"""
        return self.model.query.filter_by(role='teacher', is_active=True)\
            .join(User.teacher_profile).all()
    
    def get_students_list(self) -> List[User]:
        """Get all students with their profiles"""
        return self.model.query.filter_by(role='student', is_active=True)\
            .join(User.student_profile).all()
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = self.get_by_email(email)
        if user and user.verify_password(password) and user.is_active:
            return user
        return None
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_by_id(user_id)
        if user and user.verify_password(old_password):
            user.set_password(new_password)
            db.session.commit()
            return True
        return False
    
    def reset_password(self, email: str, new_password: str) -> bool:
        """Reset password for a user"""
        user = self.get_by_email(email)
        if user:
            user.set_password(new_password)
            db.session.commit()
            return True
        return False
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account"""
        return self.update(user_id, is_active=True)
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account"""
        return self.update(user_id, is_active=False)
    
    def get_user_count_by_role(self) -> Dict[str, int]:
        """Get count of users by role"""
        results = db.session.query(
            User.role, 
            db.func.count(User.id)
        ).group_by(User.role).all()
        return {role: count for role, count in results}
    
    def get_recent_users(self, limit: int = 10) -> List[User]:
        """Get recently created users"""
        return self.model.query.order_by(User.created_at.desc()).limit(limit).all()