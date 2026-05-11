from .base_repository import BaseRepository
from app.models.teacher import Teacher, teacher_classes
from app.models.user import User
from app import db
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, or_

class TeacherRepository(BaseRepository):
    """Repository for Teacher model with specific queries"""
    
    def __init__(self):
        super().__init__(Teacher)
    
    def get_by_user_id(self, user_id: int) -> Optional[Teacher]:
        """Get teacher profile by user ID"""
        return self.model.query.filter_by(user_id=user_id).first()
    
    def get_by_employee_id(self, employee_id: str) -> Optional[Teacher]:
        """Get teacher by employee ID"""
        return self.model.query.filter_by(employee_id=employee_id).first()
    
    def get_teachers_by_subject(self, subject: str) -> List[Teacher]:
        """Get teachers by subject"""
        return self.model.query.filter(
            self.model.subject.ilike(f'%{subject}%')
        ).all()
    
    def get_teachers_by_class(self, class_id: int) -> List[Teacher]:
        """Get teachers assigned to a specific class"""
        return self.model.query.join(
            teacher_classes, teacher_classes.c.teacher_id == self.model.id
        ).filter(teacher_classes.c.class_id == class_id).all()
    
    def get_class_teachers(self) -> List[Teacher]:
        """Get teachers who are class teachers"""
        from app.models.school_class import SchoolClass
        class_teacher_ids = db.session.query(SchoolClass.class_teacher_id).distinct()
        return self.model.query.filter(self.model.id.in_(class_teacher_ids)).all()
    
    def assign_to_class(self, teacher_id: int, class_id: int) -> bool:
        """Assign a teacher to a class"""
        teacher = self.get_by_id(teacher_id)
        if teacher:
            from app.models.school_class import SchoolClass
            school_class = SchoolClass.query.get(class_id)
            if school_class:
                teacher.classes_teaching.append(school_class)
                db.session.commit()
                return True
        return False
    
    def remove_from_class(self, teacher_id: int, class_id: int) -> bool:
        """Remove a teacher from a class"""
        teacher = self.get_by_id(teacher_id)
        if teacher:
            from app.models.school_class import SchoolClass
            school_class = SchoolClass.query.get(class_id)
            if school_class and school_class in teacher.classes_teaching:
                teacher.classes_teaching.remove(school_class)
                db.session.commit()
                return True
        return False
    
    def get_available_teachers(self) -> List[Teacher]:
        """Get teachers not assigned as class teachers"""
        from app.models.school_class import SchoolClass
        assigned_teacher_ids = db.session.query(SchoolClass.class_teacher_id).filter(
            SchoolClass.class_teacher_id.isnot(None)
        ).distinct()
        return self.model.query.filter(~self.model.id.in_(assigned_teacher_ids)).all()
    
    def get_teacher_schedule(self, teacher_id: int) -> Dict[str, Any]:
        """Get teacher's class schedule"""
        teacher = self.get_by_id(teacher_id)
        if teacher:
            return {
                'teacher': teacher.to_dict(),
                'classes': [school_class.to_dict() for school_class in teacher.classes_teaching],
                'as_class_teacher_of': [school_class.to_dict() for school_class in teacher.classes_as_class_teacher]
            }
        return None
    
    def get_teacher_attendance_summary(self, teacher_id: int, start_date, end_date) -> Dict[str, Any]:
        """Get attendance marked by teacher in date range"""
        from app.models.attendance import Attendance
        
        attendance_records = Attendance.query.filter(
            Attendance.marked_by_id == teacher_id,
            Attendance.date.between(start_date, end_date)
        ).all()
        
        return {
            'teacher_id': teacher_id,
            'start_date': start_date,
            'end_date': end_date,
            'total_records_marked': len(attendance_records),
            'records': [record.to_dict() for record in attendance_records]
        }
    
    def search_teachers(self, search_term: str) -> List[Teacher]:
        """Search teachers by name, employee_id, or subject"""
        return self.model.query.join(User).filter(
            or_(
                User.first_name.ilike(f'%{search_term}%'),
                User.last_name.ilike(f'%{search_term}%'),
                self.model.employee_id.ilike(f'%{search_term}%'),
                self.model.subject.ilike(f'%{search_term}%')
            )
        ).all()