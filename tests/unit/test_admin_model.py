# tests/unit/test_admin_model.py
"""
Unit tests for admin-related model functionality.
Tests the is_admin field on the User model.
"""
from models import User


def test_new_user_is_not_admin_by_default(test_app, init_database):
    """
    GIVEN a User model
    WHEN a new User is created and saved to the database
    THEN is_admin should be False by default
    """
    with test_app.app_context():
        from extensions import db
        
        user = User(username='newadminuser', email='newadmin@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Re-fetch from database to check default was applied
        saved_user = User.query.filter_by(username='newadminuser').first()
        assert saved_user.is_admin == False


def test_user_can_be_made_admin(test_app, init_database):
    """
    GIVEN an existing User
    WHEN is_admin is set to True
    THEN the user should be an admin
    """
    with test_app.app_context():
        from extensions import db
        
        user = User.query.filter_by(username='testuser').first()
        assert user.is_admin == False
        
        user.is_admin = True
        db.session.commit()
        
        # Re-fetch to confirm persistence
        user = User.query.filter_by(username='testuser').first()
        assert user.is_admin == True


def test_admin_can_be_revoked(test_app, init_database):
    """
    GIVEN an admin User
    WHEN is_admin is set to False
    THEN the user should no longer be an admin
    """
    with test_app.app_context():
        from extensions import db
        
        user = User.query.filter_by(username='testuser').first()
        user.is_admin = True
        db.session.commit()
        
        # Revoke admin
        user.is_admin = False
        db.session.commit()
        
        # Re-fetch to confirm
        user = User.query.filter_by(username='testuser').first()
        assert user.is_admin == False


def test_is_admin_field_persists_correctly(test_app, init_database):
    """
    GIVEN a User model
    WHEN is_admin is set and saved
    THEN it should persist correctly in the database
    """
    with test_app.app_context():
        from extensions import db
        
        # Create a user and make them admin
        user = User(username='persisttest', email='persist@example.com')
        user.set_password('password123')
        user.is_admin = True
        db.session.add(user)
        db.session.commit()
        
        # Re-fetch and verify
        saved_user = User.query.filter_by(username='persisttest').first()
        assert saved_user.is_admin == True
