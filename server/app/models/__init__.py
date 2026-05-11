from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher, teacher_classes
from app.models.school_class import SchoolClass
from app.models.attendance import Attendance

# Define what gets exported when using `from app.models import *`
__all__ = [
    'User', 
    'Student', 
    'Teacher', 
    'teacher_classes',
    'SchoolClass', 
    'Attendance'
]

# Optional: Create a function to get all models for database operations
def get_all_models():
    """Return a list of all models for database operations"""
    return [User, Student, Teacher, SchoolClass, Attendance]

# Optional: Model registry for easy access
MODEL_REGISTRY = {
    'user': User,
    'student': Student,
    'teacher': Teacher,
    'school_class': SchoolClass,
    'attendance': Attendance,
}