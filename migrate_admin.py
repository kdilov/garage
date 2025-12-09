# migrate_admin.py
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        result = db.session.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'is_admin' not in columns:
            db.session.execute(text('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL'))
            db.session.commit()
            print("✅ Added is_admin column to users table")
        else:
            print("ℹ️  is_admin column already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()