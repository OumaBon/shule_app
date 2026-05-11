from .base_repository import BaseRepository
from app.models.student import Student
from app import db
from typing import Optional, List, Dict
from datetime import date

class StudentRepository(BaseRepository):
    """Repository for Student model with specific queries"""
    
    def __init__(self):
        super().__init__(Student)
    
    def get_by_admission_number(self, admission_number: str) -> Optional[Student]:
        """Get student by admission number"""
        return self.model.query.filter_by(admission_number=admission_number).first()
    
    def get_by_user_id(self, user_id: int) -> Optional[Student]:
        """Get student profile by user ID"""
        return self.model.query.filter_by(user_id=user_id).first()
    
    def get_students_by_class(self, class_id: int) -> List[Student]:
        """Get all students in a class"""
        return self.model.query.filter_by(class_id=class_id).all()
    
    def get_students_by_guardian(self, guardian_name: str) -> List[Student]:
        """Get students by guardian name"""
        return self.model.query.filter(
            self.model.guardian_name.ilike(f'%{guardian_name}%')
        ).all()
    
    def get_students_born_between(self, start_date: date, end_date: date) -> List[Student]:
        """Get students born in date range"""
        return self.model.query.filter(
            self.model.date_of_birth.between(start_date, end_date)
        ).all()
    
    def get_students_with_no_attendance(self, class_id: int, attendance_date: date) -> List[Student]:
        """Get students who don't have attendance record for a specific date"""
        from app.models.attendance import Attendance
        
        subquery = db.session.query(Attendance.student_id).filter(
            Attendance.date == attendance_date
        ).subquery()
        
        return self.model.query.filter(
            self.model.class_id == class_id,
            self.model.id.notin_(subquery)
        ).all()
    
    def transfer_student(self, student_id: int, new_class_id: int) -> Optional[Student]:
        """Transfer student to another class"""
        student = self.get_by_id(student_id)
        if student:
            student.class_id = new_class_id
            db.session.commit()
            return student
        return None
    
    def get_student_attendance_summary(self, student_id: int, start_date: date, end_date: date) -> Dict:
        """Get attendance summary for a student"""
        from app.models.attendance import Attendance
        
        attendance_records = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.date.between(start_date, end_date)
        ).all()
        
        total = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == 'present')
        absent = sum(1 for r in attendance_records if r.status == 'absent')
        late = sum(1 for r in attendance_records if r.status == 'late')
        
        return {
            'student_id': student_id,
            'start_date': start_date,
            'end_date': end_date,
            'total_records': total,
            'present': present,
            'absent': absent,
            'late': late,
            'attendance_rate': (present / total * 100) if total > 0 else 0
        }