# src/garage/__main__.py
"""Entry point for running the application with `python -m garage`."""
import os

from garage import create_app
from garage.extensions import db


def main():
    """Run the development server."""
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("✅ Database tables ready")
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8005))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n🚀 Starting Garage Inventory")
    print(f"📍 Running on http://{host}:{port}/")
    if debug:
        print("🔧 Debug mode is ON")
    print("⏹️  Press CTRL+C to stop\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
