from app import db
from datetime import datetime, date
from sqlalchemy import UniqueConstraint, Index, func
from typing import Optional, Dict

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(db.String(10), nullable=False, index=True)  # present, absent, late, excused
    marked_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    remarks = db.Column(db.String(200), nullable=True)
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one attendance record per student per day
    __table_args__ = (
        UniqueConstraint('student_id', 'date', name='unique_student_attendance_per_day'),
        Index('idx_attendance_date_status', 'date', 'status'),
        Index('idx_attendance_student_date', 'student_id', 'date'),
        Index('idx_attendance_marked_by', 'marked_by_id', 'date'),
    )
    
    # Status constants
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'
    STATUS_EXCUSED = 'excused'
    
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_EXCUSED, 'Excused'),
    ]
    
    # Relationships
    student = db.relationship('Student', back_populates='attendance_records')
    marked_by = db.relationship('Teacher', back_populates='marked_attendance')
    
    @property
    def status_display(self) -> str:
        """Get human-readable status"""
        status_map = {
            self.STATUS_PRESENT: 'Present',
            self.STATUS_ABSENT: 'Absent',
            self.STATUS_LATE: 'Late',
            self.STATUS_EXCUSED: 'Excused'
        }
        return status_map.get(self.status, 'Unknown')
    
    @property
    def is_present(self) -> bool:
        """Check if student was present"""
        return self.status == self.STATUS_PRESENT
    
    @property
    def is_absent(self) -> bool:
        """Check if student was absent"""
        return self.status == self.STATUS_ABSENT
    
    @property
    def is_late(self) -> bool:
        """Check if student was late"""
        return self.status == self.STATUS_LATE
    
    @classmethod
    def get_status_choices(cls):
        """Get status choices for forms"""
        return cls.STATUS_CHOICES
    
    def mark_present(self, check_in_time: Optional[str] = None):
        """Mark attendance as present"""
        self.status = self.STATUS_PRESENT
        if check_in_time:
            self.check_in_time = check_in_time
    
    def mark_absent(self):
        """Mark attendance as absent"""
        self.status = self.STATUS_ABSENT
    
    def mark_late(self, check_in_time: str):
        """Mark attendance as late"""
        self.status = self.STATUS_LATE
        self.check_in_time = check_in_time
    
    def mark_excused(self, remarks: str = None):
        """Mark attendance as excused"""
        self.status = self.STATUS_EXCUSED
        if remarks:
            self.remarks = remarks
    
    def to_dict(self, include_student: bool = False, include_teacher: bool = False):
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'status_display': self.status_display,
            'marked_by_id': self.marked_by_id,
            'remarks': self.remarks,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_student and self.student:
            data['student'] = self.student.to_dict()
        
        if include_teacher and self.marked_by:
            data['marked_by'] = self.marked_by.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<Attendance Student:{self.student_id} Date:{self.date} Status:{self.status}>'