# src/garage/__main__.py
"""
Entry point for running the application directly.

This allows running the app with:
    python -m garage
    
Or with uv:
    uv run python -m garage

This is an alternative to using Flask's CLI:
    flask --app garage:create_app run
"""
import os

from garage import create_app
from garage.extensions import db


def main():
    """Run the application."""
    # Create the app
    app = create_app()
    
    # Ensure database tables exist
    with app.app_context():
        db.create_all()
        print("✅ Database tables ready")
    
    # Get server configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8005))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Print startup message
    print(f"\n🚀 Starting Garage Inventory")
    print(f"📍 Running on http://{host}:{port}/")
    if debug:
        print("🔧 Debug mode is ON")
    print("⏹️  Press CTRL+C to stop\n")
    
    # Run the app
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()