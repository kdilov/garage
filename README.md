# Garage Inventory System

A Flask web application for managing storage boxes using QR codes. Scan a box with your phone to instantly see what's inside.

## Features

- **User Authentication** - Secure registration and login
- **Box Management** - Create, edit, and delete storage boxes
- **Image Upload** - Add photos to boxes (local or S3 storage)
- **Item Tracking** - Track items with quantity, category, and value
- **QR Code Generation** - Auto-generated QR codes for each box
- **Mobile QR Scanner** - Scan QR codes using your phone's camera
- **Search** - Find boxes and items by name, location, or category
- **Admin Dashboard** - Flask-Admin panel for administrators

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Admin
- **Database:** SQLite (development) / PostgreSQL (production)
- **Storage:** Local filesystem (development) / AWS S3 (production)
- **Frontend:** Bootstrap 5, Jinja2
- **Deployment:** Heroku, Gunicorn

## Project Structure

```
garage-inventory/
├── src/garage/              # Application package
│   ├── __init__.py          # App factory (create_app)
│   ├── __main__.py          # Entry point for python -m garage
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions
│   ├── forms.py             # WTForms definitions
│   ├── admin.py             # Flask-Admin setup
│   ├── logging_config.py    # Structured logging
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── box.py
│   │   └── item.py
│   ├── routes/              # Route blueprints
│   │   ├── auth.py          # Login, register, password reset
│   │   ├── boxes.py         # Box CRUD
│   │   ├── items.py         # Item CRUD
│   │   ├── scanner.py       # QR scanning, search
│   │   └── main.py          # Landing page, health check
│   ├── services/            # Business logic
│   │   ├── email_service.py
│   │   ├── qr_service.py
│   │   └── storage/         # File storage backends
│   │       ├── base.py      # Abstract interface
│   │       ├── local.py     # Local filesystem
│   │       ├── s3.py        # AWS S3
│   │       └── factory.py   # Backend selection
│   └── utils/
│       └── decorators.py    # @owns_box, @owns_item
├── templates/               # Jinja2 templates
├── static/                  # Static files (CSS, images, QR codes)
├── tests/                   # Test suite
├── pyproject.toml           # Dependencies and project config
├── Procfile                 # Heroku process definition
└── .env                     # Environment variables (not in git)
```

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Local Development

1. Clone and install dependencies:
   ```bash
   git clone <repo-url>
   cd garage-inventory
   uv sync
   ```

2. Create `.env` file:
   ```bash
   FLASK_ENV=development
   SECRET_KEY=dev-secret-key
   ```

3. Run the application:
   ```bash
   uv run python -m garage
   ```

4. Open http://localhost:8005

### Running with Flask CLI

```bash
flask --app garage:create_app run --port 8005
```

## Configuration

Configuration is managed through environment variables and `src/garage/config.py`.

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (`development`, `production`, `testing`) | `development` |
| `SECRET_KEY` | Flask secret key | Required in production |
| `DATABASE_URL` | Database connection string | SQLite in development |
| `STORAGE_BACKEND` | `local` or `s3` | `local` in dev, `s3` in prod |
| `S3_BUCKET_NAME` | AWS S3 bucket name | Required if using S3 |
| `S3_REGION` | AWS region | `eu-west-2` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required if using S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required if using S3 |

## Production Deployment (Heroku)

1. Create Heroku app:
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-postgresql:essential-0
   ```

2. Set environment variables:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secure-secret-key
   heroku config:set STORAGE_BACKEND=s3
   heroku config:set S3_BUCKET_NAME=your-bucket
   heroku config:set S3_REGION=eu-west-2
   heroku config:set AWS_ACCESS_KEY_ID=your-key
   heroku config:set AWS_SECRET_ACCESS_KEY=your-secret
   ```

3. Deploy:
   ```bash
   git push heroku main
   ```

4. Run database migrations:
   ```bash
   heroku run python -c "from garage import create_app; from garage.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

## Admin Access

To grant admin privileges:

```bash
heroku pg:psql -c "UPDATE users SET is_admin = true WHERE username = 'your-username';"
```

Then access the admin panel at `/admin/`.

## Testing

```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=src/garage --cov-report=html
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/health` | GET | Health check (returns JSON) |
| `/register` | GET, POST | User registration |
| `/login` | GET, POST | User login |
| `/logout` | GET | User logout |
| `/dashboard` | GET | List user's boxes |
| `/box/create` | GET, POST | Create new box |
| `/box/<id>` | GET | View box details |
| `/box/<id>/edit` | GET, POST | Edit box |
| `/box/<id>/delete` | POST | Delete box |
| `/box/<id>/item/create` | GET, POST | Add item to box |
| `/item/<id>/edit` | GET, POST | Edit item |
| `/item/<id>/delete` | POST | Delete item |
| `/scan` | GET | QR scanner page |
| `/qr/<id>` | GET | QR code redirect |
| `/search` | GET | Search boxes and items |

## License

MIT
