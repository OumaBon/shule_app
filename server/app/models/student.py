from app import db
from datetime import date, datetime

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    admission_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    guardian_name = db.Column(db.String(200), nullable=False)
    guardian_phone = db.Column(db.String(20), nullable=False)
    date_enrolled = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='student_profile')
    class_obj = db.relationship('SchoolClass', back_populates='students')
    attendance_records = db.relationship('Attendance', back_populates='student', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_student_class', 'class_id'),
        db.Index('idx_student_admission', 'admission_number'),
    )
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'admission_number': self.admission_number,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'class_id': self.class_id,
            'guardian_name': self.guardian_name,
            'guardian_phone': self.guardian_phone,
            'date_enrolled': self.date_enrolled.isoformat() if self.date_enrolled else None,
            'user': self.user.to_dict() if self.user else None
        }