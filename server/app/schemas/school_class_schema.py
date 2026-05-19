# app/schemas/school_class_schema.py

from app.models.school_class import SchoolClass
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import fields, validate, validates, ValidationError, pre_load, validates_schema, post_load
from app import db
from datetime import datetime


class SchoolClassSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass
        load_instance = True 
        include_fk = True     
        include_relationships = False  
        sqla_session = db.session
    
    # Auto fields
    id = auto_field(dump_only=True)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)
    
    # String fields with validation
    name = fields.String(
        required=True,
        validate=[
            validate.Length(min=2, max=50, error="Class name must be between 2 and 50 characters"),
            validate.Regexp(
                r'^[A-Za-z0-9\s\-]+$',
                error="Class name must contain only letters, numbers, spaces and hyphens"
            )
        ]
    )
    
    year = fields.Integer(
        required=True,
        validate=validate.Range(
            min=2000, 
            max=2100, 
            error="Year must be between 2000 and 2100"
        )
    )
    
    class_teacher_id = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=1, error="Invalid teacher ID")
    )
    
    capacity = fields.Integer(
        required=True,
        validate=validate.Range(
            min=1, 
            max=100, 
            error="Capacity must be between 1 and 100 students"
        )
    )
    
    description = fields.String(
        allow_none=True,
        validate=validate.Length(max=500, error="Description must be less than 500 characters")
    )
    
    room_number = fields.String(
        allow_none=True,
        validate=validate.Length(max=20, error="Room number must be less than 20 characters")
    )
    
    is_active = fields.Boolean(
        load_default=True
    )
    
    # Computed fields (read-only)
    current_enrollment = fields.Integer(dump_only=True)
    available_seats = fields.Integer(dump_only=True)
    is_full = fields.Boolean(dump_only=True)
    class_teacher_name = fields.String(dump_only=True)
    
    @validates_schema
    def validate_class(self, data, **kwargs):
        """Cross-field validation for class"""
        # Validate unique class name and year combination
        if 'name' in data and 'year' in data:
            name = data['name']
            year = data['year']
            
            query = SchoolClass.query.filter(
                SchoolClass.name == name,
                SchoolClass.year == year
            )
            
            # Exclude current instance when updating
            if self.instance:
                query = query.filter(SchoolClass.id != self.instance.id)
            
            if query.first():
                raise ValidationError(
                    f"Class '{name}' already exists for year {year}",
                    field_name="name"
                )
        
        # Validate class_teacher_id exists and is not already assigned
        if 'class_teacher_id' in data and data['class_teacher_id'] is not None:
            teacher_id = data['class_teacher_id']
            from app.models.teacher import Teacher
            
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                raise ValidationError(
                    f"Teacher with ID {teacher_id} does not exist",
                    field_name="class_teacher_id"
                )
            
            # Check if teacher is already a class teacher for another class
            existing_class = SchoolClass.query.filter(
                SchoolClass.class_teacher_id == teacher_id,
                SchoolClass.id != (self.instance.id if self.instance else None),
                SchoolClass.is_active == True
            ).first()
            
            if existing_class:
                raise ValidationError(
                    f"Teacher is already assigned as class teacher for '{existing_class.name}'",
                    field_name="class_teacher_id"
                )
        
        # More flexible year validation
        if 'year' in data:
            current_year = datetime.now().year
            # Allow years from 2000 to current_year + 5
            if data['year'] < 2000:
                raise ValidationError(
                    "Year must be 2000 or later",
                    field_name="year"
                )
            if data['year'] > current_year + 5:
                raise ValidationError(
                    f"Year cannot be more than 5 years in the future",
                    field_name="year"
                )
        
        return data
    
    @pre_load
    def process_input(self, data, **kwargs):
        """Clean and normalize input data before validation"""
        if isinstance(data, dict):
            # Strip whitespace from string fields
            for field in ['name', 'description', 'room_number']:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
            
            # Title case class name
            if 'name' in data and isinstance(data['name'], str):
                data['name'] = data['name'].title()
            
            # Convert empty strings to None for optional fields
            for field in ['description', 'room_number', 'class_teacher_id']:
                if field in data and data[field] == '':
                    data[field] = None
            
            # Ensure year is integer
            if 'year' in data and isinstance(data['year'], str):
                try:
                    data['year'] = int(data['year'])
                except ValueError:
                    pass  # Let validation handle the error
            
            # Set default capacity if not provided
            if 'capacity' not in data:
                data['capacity'] = 40
        
        return data
    
    # REMOVED post_load_processing or FIXED it
    # When load_instance=True, post_load receives the model instance, not a dict
    # @post_load is not needed here since defaults are handled in @pre_load


# Compact schema for lists
class SchoolClassListSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass
        load_instance = True
        include_fk = True
        include_relationships = False
        sqla_session = db.session
        fields = ('id', 'name', 'year', 'class_teacher_name', 'capacity', 
                 'current_enrollment', 'available_seats', 'is_full', 
                 'room_number', 'is_active')
    
    class_teacher_name = fields.String(dump_only=True)
    current_enrollment = fields.Integer(dump_only=True)
    available_seats = fields.Integer(dump_only=True)
    is_full = fields.Boolean(dump_only=True)


# Schema for enrollment details
class SchoolClassEnrollmentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass
        load_instance = True
        include_fk = True
        include_relationships = False
        sqla_session = db.session
        fields = ('id', 'name', 'year', 'capacity', 'current_enrollment', 
                 'available_seats', 'is_full')
    
    current_enrollment = fields.Integer(dump_only=True)
    available_seats = fields.Integer(dump_only=True)
    is_full = fields.Boolean(dump_only=True)


# Create schema instances
class_schema = SchoolClassSchema()
classes_schema = SchoolClassSchema(many=True)
class_list_schema = SchoolClassListSchema()
classes_list_schema = SchoolClassListSchema(many=True)
class_enrollment_schema = SchoolClassEnrollmentSchema()