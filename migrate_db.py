# migrate_db.py
from garage import create_app
from garage.extensions import db

app = create_app()
with app.app_context():
    db.session.execute(db.text('ALTER TABLE boxes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP'))
    db.session.execute(db.text('ALTER TABLE items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP'))
    db.session.commit()
    print('Columns added successfully!')