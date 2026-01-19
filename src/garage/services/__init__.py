# src/garage/services/__init__.py
"""
Business logic services.

WHY SERVICES:
Your app.py currently has business logic mixed with route handlers.
For example, send_password_reset_email() and generate_qr_code() are
functions that do real work, not just handle HTTP requests.

Services separate "what to do" from "how to respond to HTTP":
- Routes: Handle HTTP (get form data, return responses, redirects)
- Services: Do the actual work (send emails, generate images, save files)

BENEFITS:
1. Routes become thin and easy to read
2. Services can be reused (CLI commands, background jobs, etc.)
3. Services are easier to test (no HTTP mocking needed)
4. Clear separation of concerns

USAGE:
    from garage.services import EmailService, QRService
    
    EmailService.send_password_reset(user)
    QRService.generate_for_box(box_id)
"""
from garage.services.email_service import EmailService
from garage.services.qr_service import QRService

__all__ = ['EmailService', 'QRService']