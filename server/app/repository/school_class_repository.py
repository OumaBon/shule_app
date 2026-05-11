from .base_repository import BaseRepository
from app.models.school_class import SchoolClass
from app.models.teacher import Teacher
from app.models.student import Student
from app import db
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, or_, func

class ClassRepository(BaseRepository):
    """Repository for SchoolClass model with specific queries"""
    
    def __init__(self):
        super().__init__(SchoolClass)
    
    def get_by_name_and_year(self, name: str, year: int) -> Optional[SchoolClass]:
        """Get class by name and year"""
        return self.model.query.filter_by(name=name, year=year).first()
    
    def get_classes_by_year(self, year: int, is_active: bool = True) -> List[SchoolClass]:
        """Get all classes for a specific year"""
        return self.model.query.filter_by(year=year, is_active=is_active).all()
    
    def get_classes_by_teacher(self, teacher_id: int) -> List[SchoolClass]:
        """Get classes taught by a specific teacher"""
        return self.model.query.filter(
            or_(
                SchoolClass.class_teacher_id == teacher_id,
                SchoolClass.teachers.any(id=teacher_id)
            )
        ).all()
    
    def get_full_classes(self) -> List[SchoolClass]:
        """Get classes that are full"""
        classes = self.get_all()
        return [c for c in classes if c.is_full]
    
    def get_classes_with_available_seats(self) -> List[SchoolClass]:
        """Get classes with available seats"""
        classes = self.get_all()
        return [c for c in classes if not c.is_full]
    
    def assign_class_teacher(self, class_id: int, teacher_id: int) -> Optional[SchoolClass]:
        """Assign a class teacher to a class"""
        school_class = self.get_by_id(class_id)
        teacher = Teacher.query.get(teacher_id)
        if school_class and teacher:
            school_class.class_teacher_id = teacher_id
            db.session.commit()
            return school_class
        return None
    
    def get_class_students_with_details(self, class_id: int) -> List[Student]:
        """Get all students in a class with their details"""
        school_class = self.get_by_id(class_id)
        if school_class:
            return school_class.students.all()
        return []
    
    def get_class_statistics(self, class_id: int) -> Dict[str, Any]:
        """Get statistics for a class"""
        school_class = self.get_by_id(class_id)
        if not school_class:
            return {}
        
        students = school_class.students.all()
        total_students = len(students)
        male_count = sum(1 for s in students if s.gender == 'M')
        female_count = sum(1 for s in students if s.gender == 'F')
        
        # Calculate age distribution
        from datetime import date
        ages = []
        for student in students:
            if student.date_of_birth:
                age = date.today().year - student.date_of_birth.year
                ages.append(age)
        
        return {
            'class_id': school_class.id,
            'class_name': school_class.name,
            'year': school_class.year,
            'total_students': total_students,
            'capacity': school_class.capacity,
            'available_seats': school_class.available_seats,
            'occupancy_rate': (total_students / school_class.capacity * 100) if school_class.capacity > 0 else 0,
            'gender_distribution': {
                'male': male_count,
                'female': female_count,
                'other': total_students - male_count - female_count
            },
            'age_distribution': {
                'min_age': min(ages) if ages else None,
                'max_age': max(ages) if ages else None,
                'average_age': sum(ages) / len(ages) if ages else None
            },
            'class_teacher': school_class.class_teacher.to_dict() if school_class.class_teacher else None
        }
    
    def transfer_students(self, from_class_id: int, to_class_id: int, student_ids: List[int]) -> bool:
        """Transfer multiple students from one class to another"""
        try:
            to_class = self.get_by_id(to_class_id)
            if not to_class or to_class.is_full:
                return False
            
            students = Student.query.filter(Student.id.in_(student_ids)).all()
            for student in students:
                if student.class_id == from_class_id:
                    student.class_id = to_class_id
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def archive_class(self, class_id: int) -> Optional[SchoolClass]:
        """Archive a class (soft delete)"""
        return self.update(class_id, is_active=False)
    
    def restore_class(self, class_id: int) -> Optional[SchoolClass]:
        """Restore an archived class"""
        return self.update(class_id, is_active=True)
    
    def search_classes(self, search_term: str, year: int = None) -> List[SchoolClass]:
        """Search classes by name or year"""
        query = self.model.query.filter(
            SchoolClass.name.ilike(f'%{search_term}%')
        )
        if year:
            query = query.filter(SchoolClass.year == year)
        return query.all()
    
    def get_classes_summary(self, year: int = None) -> List[Dict[str, Any]]:
        """Get summary of all classes"""
        query = self.model.query
        if year:
            query = query.filter(SchoolClass.year == year)
        
        classes = query.all()
        summary = []
        for school_class in classes:
            total_students = school_class.current_enrollment
            summary.append({
                'id': school_class.id,
                'name': school_class.name,
                'year': school_class.year,
                'total_students': total_students,
                'capacity': school_class.capacity,
                'available_seats': school_class.available_seats,
                'class_teacher': school_class.get_class_teacher_name()
            })
        return summary