#!/usr/bin/env python3
import os
from app import create_app, db
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

# Add custom CLI commands
@app.cli.command("init-db")
def init_db():
    """Initialize database and create all tables"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

@app.cli.command("seed-db")
def seed_db():
    """Seed database with initial data"""
    from app.models.model import User, Teacher, Student, SchoolClass
    from datetime import date
    
    with app.app_context():
        # Check if admin exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                email='admin@school.com',
                username='admin',
                first_name='Admin',
                last_name='User',
                role='admin',
                phone='1234567890',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin@school.com / admin123")
        else:
            print("ℹ️ Admin user already exists")

if __name__ == '__main__':
    app.run()