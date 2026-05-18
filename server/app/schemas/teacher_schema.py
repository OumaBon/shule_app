from app.models.teacher import Teacher
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import fields, validate, validates, ValidationError, pre_load, validates_schema

from app import db
from marshmallow import pre_load
from datetime import date




class TeacherSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher
        load_instance = True 
        include_fk = True     
        include_relationships = False  
        sqla_session = db.session
    
   
    id = auto_field(dump_only=True)  
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)
    
   
    employee_id = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=20, error="Employee ID must be between 3 and 20 characters"),
            validate.Regexp(
                r'^[A-Z0-9\-_]+$', 
                error="Employee ID must contain only uppercase letters, numbers, hyphens and underscores"
            )
        ]
    )
    
    subject = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Subject must be between 2 and 100 characters")
    )
    
    qualification = fields.String(
        validate=validate.Length(max=200, error="Qualification must be less than 200 characters"),
        allow_none=True
    )
    
    date_joined = fields.Date(
        allow_none=True
    )
    
    user_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Invalid user ID")
    )
    
    
    @validates_schema
    def validate_teacher(self, data, **kwargs):
        """Cross-field validation for teacher"""
        if 'employee_id' in data and data['employee_id']:
            employee_id = data['employee_id']
            from app.models.teacher import Teacher
            query = Teacher.query.filter(Teacher.employee_id == employee_id)
            if self.instance:  
                query = query.filter(Teacher.id != self.instance.id)
            if query.first():
                raise ValidationError(
                    f"Employee ID '{employee_id}' already exists",
                    field_name="employee_id"
                )
        
        # Validate user_id existence and uniqueness
        if 'user_id' in data and data['user_id']:
            user_id = data['user_id']
            from app.models.user import User  
            user = User.query.get(user_id)
            if not user:
                raise ValidationError(
                    f"User with ID {user_id} does not exist",
                    field_name="user_id"
                )
            
            from app.models.teacher import Teacher
            query = Teacher.query.filter(Teacher.user_id == user_id)
            if self.instance:  
                query = query.filter(Teacher.id != self.instance.id)
            if query.first():
                raise ValidationError(
                    "User already has a teacher profile",
                    field_name="user_id"
                )
        
        # Validate date_joined is not in the future
        if 'date_joined' in data and data['date_joined']:
            if data['date_joined'] > date.today():
                raise ValidationError(
                    "Date joined cannot be in the future",
                    field_name="date_joined"
                )
        
        return data
    
    
    @pre_load
    def process_input(self, data, **kwargs):
        """Clean and normalize input data before validation"""
        if isinstance(data, dict):
            # Strip whitespace from string fields
            for field in ['employee_id', 'subject', 'qualification']:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
            
            # Convert employee_id to uppercase
            if 'employee_id' in data and isinstance(data['employee_id'], str):
                data['employee_id'] = data['employee_id'].upper()
            
            # Handle date_joined - if empty string, set to None
            if 'date_joined' in data and data['date_joined'] == '':
                data['date_joined'] = None
        
        return data


# Create schema instances
teacher_schema = TeacherSchema()
teachers_schema = TeacherSchema(many=True)