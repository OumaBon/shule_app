#!/usr/bin/env python3
import os
from app import create_app, db
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'development')
migrate = Migrate(app, db)


# Add custom CLI commands
@app.cli.command("init-db")
def init_db():
    """Initialize database and create all tables"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

# 
if __name__ == '__main__':
    app.run()