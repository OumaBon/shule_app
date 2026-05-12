import regex
from app.models.user import User 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema 
from marshmallow import fields, validate, validates, ValidationError, validates_schema 


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True 
        include_relationships = True
        exclude = ('password_hash',)  # Exclude password hash from serialization
    
    password = fields.String(load_only=True, required=True, validate=validate.Length(min=6))
    confirm_password = fields.String(load_only=True, required=True, validate=validate.Length(min=6))
    
        
    
    @validates('email')
    def validate_email(self, value, **kwargs):
        if not value:
            raise ValidationError('Email is required.')
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists.') 
        
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not regex.match(email_pattern, value):
            raise ValidationError('Invalid email format.') 
    
    
        if hasattr(self, 'instance') and self.instance: 
            if self.instance.email != value and User.query.filter_by(email=value).first():
                raise ValidationError('Email already exists.')
    
    
    @validates('username')
    def validate_username(self, value):
        if value and User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists.')
    
    
    @validates('first_name')
    def validate_first_name(self, value):
        if not value:
            raise ValidationError('First name is required.')
    
    
    @validates('last_name')
    def validate_last_name(self, value):
        if not value:
            raise ValidationError('Last name is required.')
    
    
    @validates("role")
    def validate_role(self, value):
        roles = ['student', 'teacher', 'admin']
        if value not in roles:
            raise ValidationError(f'Role must be one of {roles}.')
        if not value:
            raise ValidationError('Role is required.')
    
    
    @validates("phone") 
    def validate_phone(self, value):
        if value:
            phone_pattern = r'^\+?[1-9]\d{1,14}$'
            if not regex.match(phone_pattern, value):
                raise ValidationError('Invalid phone number format.') 
    
    
    @validates_schema
    def validate_passwords(self, data, **kwargs): 
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError('Passwords must match.', field_names=['confirm_password']) 
        
        if not password or not confirm_password:
            raise ValidationError('Password is required.', field_names=['password'])
        
        if len(password) < 6:
            raise ValidationError('Password must be at least 6 characters long.', field_names=['password'])
        
        if not regex.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.', field_names=['password'])
        
        if not regex.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.', field_names=['password'])
        
        if not regex.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one digit.', field_names=['password'])
        
        if not regex.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.', field_names=['password'])

        
        
user_schema = UserSchema()
users_schema = UserSchema(many=True)