import re
from app.models.user import User 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema 
from marshmallow import fields, validate, validates, ValidationError, validates_schema 
from app import db

import re
from app.models.user import User 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema 
from marshmallow import fields, validate, validates, ValidationError, validates_schema 
from app import db

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True 
        include_relationships = True
        exclude = ('password_hash',)  # Exclude password hash from serialization
    
    # Make password fields optional by removing required=True
    password = fields.String(load_only=True, required=False, validate=validate.Length(min=6))
    confirm_password = fields.String(load_only=True, required=False, validate=validate.Length(min=6))
    
    @validates('email')
    def validate_email(self, value, **kwargs):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError('Invalid email format.') 
    
        # Check for duplicate email
        if hasattr(self, 'instance') and self.instance: 
            if self.instance.email != value and User.query.filter_by(email=value).first():
                raise ValidationError('Email already exists.')
        else:
            if User.query.filter_by(email=value).first():
                raise ValidationError('Email already exists.')
    
    @validates('username')  
    def validate_username(self, value, **kwargs):
        if value:
            if hasattr(self, 'instance') and self.instance:
                if self.instance.username != value and User.query.filter_by(username=value).first():
                    raise ValidationError('Username already exists.')
            else:
                if User.query.filter_by(username=value).first():
                    raise ValidationError('Username already exists.')
    
    @validates('first_name')
    def validate_first_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError('First name is required.')
    
    @validates('last_name')
    def validate_last_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError('Last name is required.')
    
    @validates("role")
    def validate_role(self, value, **kwargs):
        if not value:
            raise ValidationError('Role is required.')
        
        roles = ['student', 'teacher', 'admin']
        if value not in roles:
            raise ValidationError(f'Role must be one of {roles}.')
    
    @validates("phone") 
    def validate_phone(self, value, **kwargs):
        if value:
            phone_pattern = r'^\+?[1-9]\d{1,14}$'
            if not re.match(phone_pattern, value):
                raise ValidationError('Invalid phone number format.')
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Only validate passwords if they are provided (for updates)
        if password or confirm_password:
            # If one is provided, both must be provided
            if not password or not confirm_password:
                raise ValidationError('Both password and confirm_password are required to update password.', field_names=['password'])
            
            if password != confirm_password:
                raise ValidationError('Passwords must match.', field_names=['confirm_password']) 
            
            if len(password) < 6:
                raise ValidationError('Password must be at least 6 characters long.', field_names=['password'])
            
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Password must contain at least one uppercase letter.', field_names=['password'])
            
            if not re.search(r'[a-z]', password):
                raise ValidationError('Password must contain at least one lowercase letter.', field_names=['password'])
            
            if not re.search(r'[0-9]', password):
                raise ValidationError('Password must contain at least one digit.', field_names=['password'])
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Password must contain at least one special character.', field_names=['password'])
        else:
            # For new user creation, password is required
            if not hasattr(self, 'instance') or not self.instance:
                raise ValidationError('Password is required for new users.', field_names=['password'])

user_schema = UserSchema()
users_schema = UserSchema(many=True)