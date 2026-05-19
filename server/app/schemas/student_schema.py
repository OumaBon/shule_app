from app.models.student import Student 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import fields, validate, validates, ValidationError, pre_load, validates_schema, post_load
from app import db
from datetime import date

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True 
        include_fk = True     
        include_relationships = False  
        sqla_session = db.session
    
    # Auto fields
    id = auto_field(dump_only=True)
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)
    
    # String fields with validation
    admission_number = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=20, error="Admission number must be between 3 and 20 characters"),
            validate.Regexp(
                r'^[A-Z0-9\-_/]+$',
                error="Admission number must contain only uppercase letters, numbers, hyphens, underscores and forward slashes"
            )
        ]
    )
    
    gender = fields.String(
        required=True,
        validate=validate.OneOf(
            ['Male', 'Female', 'Other'],
            error="Gender must be Male, Female, or Other"
        )
    )
    
    guardian_name = fields.String(
        required=True,
        validate=validate.Length(min=3, max=200, error="Guardian name must be between 3 and 200 characters")
    )
    
    guardian_phone = fields.String(
        required=True,
        validate=[
            validate.Length(min=10, max=20, error="Phone number must be between 10 and 20 characters"),
            validate.Regexp(
                r'^[\d\s\-\(\)\+]+$',
                error="Invalid phone number format"
            )
        ]
    )
    
    # Date fields
    date_of_birth = fields.Date(required=True)
    date_enrolled = fields.Date(allow_none=True)
    
    # Foreign key fields
    user_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Invalid user ID")
    )
    
    class_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Invalid class ID")
    )
    
    # Computed field
    age = fields.Integer(dump_only=True)
    
    @validates_schema
    def validate_student(self, data, **kwargs):
        """Cross-field validation for student"""
        # Validate unique admission number
        if 'admission_number' in data and data['admission_number']:
            admission_number = data['admission_number']
            query = Student.query.filter(Student.admission_number == admission_number)
            if self.instance:  
                query = query.filter(Student.id != self.instance.id)
            if query.first():
                raise ValidationError(
                    f"Admission number '{admission_number}' already exists",
                    field_name="admission_number"
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
            
            query = Student.query.filter(Student.user_id == user_id)
            if self.instance:  
                query = query.filter(Student.id != self.instance.id)
            if query.first():
                raise ValidationError(
                    "User already has a student profile",
                    field_name="user_id"
                )
        
        # Validate class_id existence
        if 'class_id' in data and data['class_id']:
            class_id = data['class_id']
            from app.models.school_class import SchoolClass
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                raise ValidationError(
                    f"Class with ID {class_id} does not exist",
                    field_name="class_id"
                )
        
        # Validate date of birth is in the past
        if 'date_of_birth' in data and data['date_of_birth']:
            dob = data['date_of_birth']
            if dob >= date.today():
                raise ValidationError(
                    "Date of birth must be in the past",
                    field_name="date_of_birth"
                )
            
            # Check age range (3-25 years)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 3:
                raise ValidationError(
                    "Student must be at least 3 years old",
                    field_name="date_of_birth"
                )
            if age > 25:
                raise ValidationError(
                    "Student age cannot exceed 25 years",
                    field_name="date_of_birth"
                )
        
        # Validate date_enrolled is not in the future
        if 'date_enrolled' in data and data['date_enrolled']:
            if data['date_enrolled'] > date.today():
                raise ValidationError(
                    "Enrollment date cannot be in the future",
                    field_name="date_enrolled"
                )
            
            # Validate enrollment date is after birth date if both present
            if 'date_of_birth' in data and data['date_of_birth']:
                if data['date_enrolled'] <= data['date_of_birth']:
                    raise ValidationError(
                        "Enrollment date must be after date of birth",
                        field_name="date_enrolled"
                    )
        
        return data
    
    @pre_load
    def process_input(self, data, **kwargs):
        """Clean and normalize input data before validation"""
        if isinstance(data, dict):
            # Strip whitespace from string fields
            for field in ['admission_number', 'guardian_name', 'guardian_phone', 'gender']:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
            
            # Convert admission_number to uppercase
            if 'admission_number' in data and isinstance(data['admission_number'], str):
                data['admission_number'] = data['admission_number'].upper()
            
            # Title case guardian name
            if 'guardian_name' in data and isinstance(data['guardian_name'], str):
                data['guardian_name'] = data['guardian_name'].title()
            
            # Capitalize gender
            if 'gender' in data and isinstance(data['gender'], str):
                data['gender'] = data['gender'].capitalize()
            
            # Clean phone number - remove spaces and standardize
            if 'guardian_phone' in data and isinstance(data['guardian_phone'], str):
                # Keep only digits and +
                phone = data['guardian_phone'].strip()
                data['guardian_phone'] = phone
            
            # Handle empty dates - if empty string, set to None
            for date_field in ['date_of_birth', 'date_enrolled']:
                if date_field in data and data[date_field] == '':
                    data[date_field] = None
        
        return data
    
    @post_load
    def post_load_processing(self, data, **kwargs):
        """Post-load processing for additional data manipulation"""
        partial = kwargs.get('partial', False)
        
        if not partial:
            # Additional processing for full loads if needed
            pass
        
        return data


# Compact schema for lists
class StudentListSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True
        include_fk = True
        include_relationships = False
        sqla_session = db.session
        fields = ('id', 'admission_number', 'gender', 'class_id', 
                 'guardian_name', 'guardian_phone', 'age', 'date_enrolled')
    
    age = fields.Integer(dump_only=True)


# Create schema instances
student_schema = StudentSchema()
students_schema = StudentSchema(many=True)
student_list_schema = StudentListSchema(many=True)