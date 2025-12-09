# 📦 Garage Inventory System

A Flask-based web application for managing storage boxes in your garage using QR codes. Scan a box with your phone to instantly see what's inside.

## Features

- **User Authentication** - Secure registration and login with password hashing
- **Box Management** - Create, edit, and delete storage boxes with locations and descriptions
- **Item Tracking** - Add items to boxes with quantity, category, value, and notes
- **QR Code Generation** - Automatic QR code creation for each box
- **Mobile QR Scanner** - Scan QR codes directly in your browser using your phone's camera
- **Search** - Find boxes and items by name, location, or category
- **Admin Dashboard** - Flask-Admin panel for administrators to manage all users, boxes, and items
- **Responsive Design** - Mobile-friendly Bootstrap 5 interface

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Admin
- **Database:** SQLite
- **Frontend:** Bootstrap 5, Jinja2 templates
- **QR Codes:** qrcode library (generation), html5-qrcode (scanning)
- **Testing:** pytest, pytest-flask, pytest-cov

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

1. Extract the zip file and navigate to the project folder:
   ```bash
   unzip garage-inventory.zip
   cd garage-inventory
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uv run python app.py
   ```

   Or without uv:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:8000`

## Usage

1. **Register** a new account
2. **Create boxes** representing your physical storage containers
3. **Add items** to each box with details like quantity and value
4. **Print QR codes** and attach them to your physical boxes
5. **Scan QR codes** with your phone to quickly view box contents

## Admin Setup

The application includes an admin dashboard at `/admin/` for managing all data. To grant admin privileges to a user:

### Option 1: Using Python shell

```bash
uv run python
```

```python
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(username='your_username').first()
    user.is_admin = True
    db.session.commit()
```

### Option 2: Direct database update

```bash
sqlite3 instance/inventory.db
```

```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

Once set as admin, navigate to `/admin/` to access the dashboard.

## Running Tests

```bash
uv run pytest
```

With coverage report:

```bash
uv run pytest --cov=. --cov-report=html
```

## Project Structure

```
garage-inventory/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy database models
├── forms.py            # Flask-WTF form definitions
├── admin.py            # Flask-Admin configuration
├── extensions.py       # Flask extensions initialisation
├── migrate_admin.py    # Database migration for admin field
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── boxlist.html
│   ├── boxdetail.html
│   ├── boxform.html
│   ├── itemform.html
│   ├── scanner.html
│   ├── search.html
│   └── components/
│       └── flashmessages.html
├── static/
│   └── qrcodes/        # Generated QR code images
├── tests/              # Test suite
│   ├── conftest.py
│   ├── functional/
│   └── unit/
└── pyproject.toml      # Project dependencies
```

## License

This project was created as coursework for SET09103 - Advanced Web Technologies.
