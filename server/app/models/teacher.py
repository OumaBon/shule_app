from app import db
from datetime import date, datetime

# Association table
teacher_classes = db.Table('teacher_classes',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200), nullable=True)
    date_joined = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='teacher_profile')
    classes_as_class_teacher = db.relationship('SchoolClass', back_populates='class_teacher')
    classes_teaching = db.relationship('SchoolClass', secondary=teacher_classes, back_populates='teachers')
    marked_attendance = db.relationship('Attendance', back_populates='marked_by')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'subject': self.subject,
            'qualification': self.qualification,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'user': self.user.to_dict() if self.user else None
        }