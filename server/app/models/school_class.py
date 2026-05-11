from app import db
from datetime import datetime
from typing import Optional, List

class SchoolClass(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True, index=True)
    capacity = db.Column(db.Integer, nullable=False, default=40)
    description = db.Column(db.Text, nullable=True)
    room_number = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_teacher = db.relationship('Teacher', foreign_keys=[class_teacher_id], back_populates='classes_as_class_teacher')
    students = db.relationship('Student', back_populates='class_obj', lazy='dynamic')
    teachers = db.relationship('Teacher', secondary='teacher_classes', back_populates='classes_teaching')
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_class_year_active', 'year', 'is_active'),
        db.Index('idx_class_name_year', 'name', 'year'),
    )
    
    @property
    def current_enrollment(self) -> int:
        """Get current number of students in the class"""
        return self.students.filter_by(is_active=True).count() if hasattr(self.students, 'filter_by') else len(self.students)
    
    @property
    def available_seats(self) -> int:
        """Get number of available seats in the class"""
        return self.capacity - self.current_enrollment
    
    @property
    def is_full(self) -> bool:
        """Check if class is full"""
        return self.current_enrollment >= self.capacity
    
    def can_enroll(self, student_count: int = 1) -> bool:
        """Check if class can enroll additional students"""
        return (self.current_enrollment + student_count) <= self.capacity
    
    def get_class_teacher_name(self) -> Optional[str]:
        """Get class teacher's full name"""
        if self.class_teacher and self.class_teacher.user:
            return self.class_teacher.user.full_name
        return None
    
    def to_dict(self, include_students: bool = False, include_teachers: bool = False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'class_teacher_id': self.class_teacher_id,
            'class_teacher_name': self.get_class_teacher_name(),
            'capacity': self.capacity,
            'current_enrollment': self.current_enrollment,
            'available_seats': self.available_seats,
            'is_full': self.is_full,
            'room_number': self.room_number,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_students:
            data['students'] = [student.to_dict() for student in self.students]
        
        if include_teachers:
            data['teachers'] = [teacher.to_dict() for teacher in self.teachers]
        
        return data
    
    def __repr__(self):
        return f'<SchoolClass {self.name} ({self.year})>'