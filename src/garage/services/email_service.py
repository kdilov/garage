# src/garage/services/email_service.py
"""
Email service for sending transactional emails.

WHAT THIS REPLACES:
The send_password_reset_email() function from your app.py

WHY A SERVICE CLASS:
- Groups related email functionality together
- Easy to add more email types later (welcome email, notifications, etc.)
- Logging provides visibility into email delivery
- Testable without actually sending emails

CURRENT FUNCTIONALITY:
- Password reset emails (with HTML and plain text versions)

FUTURE POSSIBILITIES:
- Welcome emails after registration
- Box sharing notifications
- Weekly inventory summaries
"""
import logging

from flask import current_app, url_for
from flask_mail import Message

from garage.extensions import mail

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending transactional emails.
    
    All methods are static because we don't need instance state.
    The Flask-Mail extension handles connection pooling.
    """
    
    @staticmethod
    def send_password_reset(user) -> bool:
        """
        Send password reset email to user.
        
        This is extracted from your original send_password_reset_email() function.
        
        Args:
            user: User model instance (needs .email, .username, .get_reset_token())
        
        Returns:
            True if sent successfully (or suppressed in dev), False on error
        """
        # Generate the reset token and URL
        token = user.get_reset_token()
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        # In development, don't actually send - just log it
        # This is controlled by MAIL_SUPPRESS_SEND config
        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info(
                "Password reset email (suppressed in development)",
                extra={
                    'user_id': user.id,
                    'email': user.email,
                }
            )
            # Print for developer convenience - they need to see the link!
            print(f"\n{'='*60}")
            print("📧 PASSWORD RESET EMAIL (Development Mode)")
            print(f"{'='*60}")
            print(f"To: {user.email}")
            print(f"Reset Link: {reset_url}")
            print(f"{'='*60}\n")
            return True
        
        # Build the email message
        msg = Message(
            subject='Password Reset Request - Garage Inventory',
            recipients=[user.email]
        )
        msg.body = EmailService._get_reset_email_text(user.username, reset_url)
        msg.html = EmailService._get_reset_email_html(user.username, reset_url)
        
        # Try to send
        try:
            mail.send(msg)
            logger.info(
                "Password reset email sent",
                extra={'user_id': user.id, 'email': user.email}
            )
            return True
            
        except Exception as e:
            # Log the error with full details for debugging
            logger.error(
                "Failed to send password reset email",
                extra={
                    'user_id': user.id,
                    'email': user.email,
                    'error': str(e)
                },
                exc_info=True  # Include stack trace
            )
            return False
    
    @staticmethod
    def _get_reset_email_text(username: str, reset_url: str) -> str:
        """
        Generate plain text email content.
        
        Plain text version is important because:
        - Some email clients don't render HTML
        - Spam filters sometimes prefer plain text
        - Accessibility (screen readers)
        """
        return f"""Hello {username},

You requested to reset your password for Garage Inventory.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Thanks,
Garage Inventory
"""

    @staticmethod
    def _get_reset_email_html(username: str, reset_url: str) -> str:
        """
        Generate HTML email content.
        
        HTML version provides better formatting and a clickable button.
        Inline styles are used because email clients strip <style> tags.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2c3e50; margin-bottom: 20px;">Password Reset Request</h2>
    
    <p>Hello {username},</p>
    
    <p>You requested to reset your password for Garage Inventory.</p>
    
    <p>Click the button below to reset your password:</p>
    
    <p style="margin: 30px 0;">
        <a href="{reset_url}" 
           style="background-color: #007bff; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;
                  font-weight: 500;">
            Reset Password
        </a>
    </p>
    
    <p style="color: #666; font-size: 14px;">
        Or copy this link: <a href="{reset_url}" style="color: #007bff;">{reset_url}</a>
    </p>
    
    <p style="color: #666; font-size: 14px;">
        <strong>This link will expire in 1 hour.</strong>
    </p>
    
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    
    <p style="color: #999; font-size: 12px;">
        If you did not request this password reset, please ignore this email.
        Your password will remain unchanged.
    </p>
</body>
</html>
"""