from .base_repository import BaseRepository
from .user_repository import UserRepository
from .student_repository import StudentRepository
from .teacher_repository import TeacherRepository
from .school_class_repository import ClassRepository
from .attendance_repository import AttendanceRepository

# Export all repositories
__all__ = [
    'BaseRepository',
    'UserRepository',
    'StudentRepository', 
    'TeacherRepository',
    'ClassRepository',
    'AttendanceRepository'
]

# Repository factory for easy access
class RepositoryFactory:
    """Factory class to get repository instances"""
    
    _repositories = {
        'user': UserRepository,
        'student': StudentRepository,
        'teacher': TeacherRepository,
        'class': ClassRepository,
        'attendance': AttendanceRepository
    }
    
    @classmethod
    def get_repository(cls, name: str):
        """Get repository instance by name"""
        repo_class = cls._repositories.get(name)
        if repo_class:
            return repo_class()
        raise ValueError(f"Unknown repository: {name}")
    
    @classmethod
    def register_repository(cls, name: str, repository_class):
        """Register a new repository"""
        cls._repositories[name] = repository_class