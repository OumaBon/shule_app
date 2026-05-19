# app/schemas/attendance_schema.py

from app.models.attendance import Attendance
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import fields, validate, validates, ValidationError, pre_load, validates_schema, post_load
from app import db
from datetime import date, datetime


class AttendanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        load_instance = True 
        include_fk = True     
        include_relationships = False  
        sqla_session = db.session
    
    # Auto fields
    id = auto_field(dump_only=True)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)
    
    # Foreign key fields
    student_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Invalid student ID")
    )
    
    marked_by_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Invalid teacher ID")
    )
    
    # Date field - FIX: Remove load_default since field is required
    date = fields.Date(
        required=True
        # Removed: load_default=date.today
    )
    
    # Status field
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ['present', 'absent', 'late', 'excused'],
            error="Status must be present, absent, late, or excused"
        )
    )
    
    # Optional fields
    remarks = fields.String(
        allow_none=True,
        validate=validate.Length(max=200, error="Remarks must be less than 200 characters")
    )
    
    check_in_time = fields.Time(allow_none=True)
    check_out_time = fields.Time(allow_none=True)
    
    # Computed fields (read-only)
    status_display = fields.String(dump_only=True)
    is_present = fields.Boolean(dump_only=True)
    is_absent = fields.Boolean(dump_only=True)
    is_late = fields.Boolean(dump_only=True)
    
    @validates_schema
    def validate_attendance(self, data, **kwargs):
        """Cross-field validation for attendance"""
        # Validate student exists
        if 'student_id' in data:
            from app.models.student import Student
            student = Student.query.get(data['student_id'])
            if not student:
                raise ValidationError(
                    f"Student with ID {data['student_id']} does not exist",
                    field_name="student_id"
                )
        
        # Validate teacher exists
        if 'marked_by_id' in data:
            from app.models.teacher import Teacher
            teacher = Teacher.query.get(data['marked_by_id'])
            if not teacher:
                raise ValidationError(
                    f"Teacher with ID {data['marked_by_id']} does not exist",
                    field_name="marked_by_id"
                )
        
        # Validate unique attendance per student per day
        if 'student_id' in data and 'date' in data:
            query = Attendance.query.filter(
                Attendance.student_id == data['student_id'],
                Attendance.date == data['date']
            )
            
            # Exclude current instance when updating
            if self.instance:
                query = query.filter(Attendance.id != self.instance.id)
            
            if query.first():
                raise ValidationError(
                    f"Attendance already marked for student on {data['date']}",
                    field_name="date"
                )
        
        # Validate date is not in the future
        if 'date' in data and data['date']:
            if data['date'] > date.today():
                raise ValidationError(
                    "Attendance date cannot be in the future",
                    field_name="date"
                )
        
        # Validate time fields based on status
        if 'status' in data:
            status = data['status']
            
            if status == 'late' and 'check_in_time' not in data:
                raise ValidationError(
                    "Check-in time is required for late status",
                    field_name="check_in_time"
                )
        
        return data
    
    @pre_load
    def process_input(self, data, **kwargs):
        """Clean and normalize input data before validation"""
        if isinstance(data, dict):
            # Strip whitespace from string fields
            for field in ['status', 'remarks']:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
            
            # Lowercase status
            if 'status' in data and isinstance(data['status'], str):
                data['status'] = data['status'].lower()
            
            # Convert empty strings to None
            for field in ['remarks', 'check_in_time', 'check_out_time']:
                if field in data and data[field] == '':
                    data[field] = None
            
            # Set default date to today if not provided
            if 'date' not in data:
                data['date'] = date.today()
        
        return data
    
    @post_load
    def post_load_processing(self, data, **kwargs):
        """Post-load processing"""
        return data


# Compact schema for lists
class AttendanceListSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        load_instance = True
        include_fk = True
        include_relationships = False
        sqla_session = db.session
        fields = ('id', 'student_id', 'date', 'status', 'status_display', 
                 'marked_by_id', 'check_in_time', 'check_out_time', 'remarks')
    
    status_display = fields.String(dump_only=True)


# Schema for bulk attendance
class BulkAttendanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        load_instance = True
        include_fk = True
        include_relationships = False
        sqla_session = db.session
    
    student_id = fields.Integer(required=True)
    status = fields.String(required=True)
    date = fields.Date()  # Not required for bulk - will be set by service
    marked_by_id = fields.Integer()  # Not required for bulk - will be set by service
    remarks = fields.String(allow_none=True)
    check_in_time = fields.Time(allow_none=True)
    check_out_time = fields.Time(allow_none=True)


# Create schema instances
attendance_schema = AttendanceSchema()
attendances_schema = AttendanceSchema(many=True)
attendance_list_schema = AttendanceListSchema()
attendances_list_schema = AttendanceListSchema(many=True)
bulk_attendance_schema = BulkAttendanceSchema(many=True)