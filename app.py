# app.py
import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from extensions import db, login_manager, mail
from models import User, Box, Item
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
import qrcode
from config import config
from storage import init_cloudinary, save_image, save_qr_image, delete_file, get_file_url
from admin import init_admin
from werkzeug.utils import secure_filename
import uuid


# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    init_admin(app)
    init_cloudinary(app)
    
    # Login manager settings
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Make get_file_url available in templates
    @app.context_processor
    def utility_processor():
        return dict(get_file_url=get_file_url)
    
    # Register routes
    register_routes(app)
    
    return app


def send_password_reset_email(user):
    """Send password reset email to user."""
    from flask import current_app
    
    token = user.get_reset_token()
    reset_url = url_for('reset_password', token=token, _external=True)
    
    # Check if email sending is suppressed (development mode)
    if current_app.config.get('MAIL_SUPPRESS_SEND', False):
        # In development, just print the link
        print("\n" + "="*60)
        print("📧 PASSWORD RESET EMAIL (Dev Mode - Not Sent)")
        print("="*60)
        print(f"To: {user.email}")
        print(f"Reset Link: {reset_url}")
        print("="*60 + "\n")
        return True
    
    msg = Message(
        subject='Password Reset Request - Garage Inventory',
        recipients=[user.email]
    )
    
    msg.body = f'''Hello {user.username},

You requested to reset your password for Garage Inventory.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Thanks,
Garage Inventory
'''
    
    msg.html = f'''
<h2>Password Reset Request</h2>
<p>Hello {user.username},</p>
<p>You requested to reset your password for Garage Inventory.</p>
<p>Click the button below to reset your password:</p>
<p style="margin: 20px 0;">
    <a href="{reset_url}" 
       style="background-color: #007bff; color: white; padding: 10px 20px; 
              text-decoration: none; border-radius: 5px;">
        Reset Password
    </a>
</p>
<p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
<p><small>This link will expire in 1 hour.</small></p>
<hr>
<p><small>If you did not request this password reset, please ignore this email.</small></p>
'''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_qr_code(app, box_id, box_name):
    """Generate a QR code for a box and return the file path/URL."""
    try:
        box_url = f"/qr/{box_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(box_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Use storage abstraction
        with app.app_context():
            return save_qr_image(img, box_id)
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None


def register_routes(app):
    """Register all routes with the app"""
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            flash('You are already registered and logged in!', 'info')
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Account created successfully for {user.username}! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            flash('You are already logged in!', 'info')
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('index'))
    
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        """Handle forgot password requests"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = ForgotPasswordForm()
        
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user:
                if send_password_reset_email(user):
                    flash('A password reset link has been sent to your email.', 'info')
                else:
                    flash('Error sending email. Please try again later.', 'danger')
            else:
                # Don't reveal if email exists or not (security)
                flash('If an account with that email exists, a reset link has been sent.', 'info')
            
            return redirect(url_for('login'))
        
        return render_template('forgotpassword.html', form=form)
    
    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        """Handle password reset with token"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        # Get expiry from config
        expiry = app.config.get('PASSWORD_RESET_EXPIRY', 3600)
        user = User.verify_reset_token(token, expiry=expiry)
        
        if user is None:
            flash('Invalid or expired reset link. Please request a new one.', 'danger')
            return redirect(url_for('forgot_password'))
        
        form = ResetPasswordForm()
        
        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            flash('Your password has been reset successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('resetpassword.html', form=form)
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        boxes = Box.query.filter_by(user_id=current_user.id).all()
        return render_template('boxlist.html', boxes=boxes)
    
    @app.route('/box/create', methods=['GET', 'POST'])
    @login_required
    def create_box():
        from forms import BoxForm
        
        form = BoxForm()
        
        if form.validate_on_submit():
            try:
                box = Box(
                    name=form.name.data,
                    location=form.location.data,
                    description=form.description.data,
                    user_id=current_user.id
                )
                
                db.session.add(box)
                db.session.flush()
                
                # Generate QR code using storage abstraction
                qr_path = generate_qr_code(app, box.id, box.name)
                box.qr_code_path = qr_path
                
                # Handle image upload
                if form.image.data:
                    image_path = save_image(form.image.data, box.id, 'box')
                    if image_path:
                        box.image_path = image_path
                
                db.session.commit()
                
                flash(f'Box "{box.name}" created successfully!', 'success')
                return redirect(url_for('view_box', box_id=box.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating box: {str(e)}', 'danger')
        
        return render_template('boxform.html', form=form, title='Create New Box')
    
    @app.route('/box/<int:box_id>', methods=['GET'])
    @login_required
    def view_box(box_id):
        box = Box.query.get_or_404(box_id)
        if box.user_id != current_user.id:
            flash('You do not have permission to view this box.', 'danger')
            return redirect(url_for('dashboard'))
        return render_template('boxdetail.html', box=box)
    
    @app.route('/box/<int:box_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_box(box_id):
        from forms import BoxForm
        box = Box.query.get_or_404(box_id)
        if box.user_id != current_user.id:
            flash('You do not have permission to edit this box.', 'danger')
            return redirect(url_for('dashboard'))
        form = BoxForm()
        if form.validate_on_submit():
            try:
                box.name = form.name.data
                box.location = form.location.data
                box.description = form.description.data
                
                # Handle image deletion
                if form.delete_image.data and box.image_path:
                    delete_file(box.image_path)
                    box.image_path = None
                # Handle new image upload
                elif form.image.data:
                    if box.image_path:
                        delete_file(box.image_path)
                    image_path = save_image(form.image.data, box.id, 'box')
                    if image_path:
                        box.image_path = image_path
                
                db.session.commit()
                flash(f'Box "{box.name}" updated successfully!', 'success')
                return redirect(url_for('view_box', box_id=box.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating box: {str(e)}', 'danger')
        elif request.method == 'GET':
            form.name.data = box.name
            form.location.data = box.location
            form.description.data = box.description
        return render_template('boxform.html', form=form, box=box, title='Edit Box')
    
    @app.route('/box/<int:box_id>/delete', methods=['POST'])
    @login_required
    def delete_box(box_id):
        box = Box.query.get_or_404(box_id)
        if box.user_id != current_user.id:
            flash('You do not have permission to delete this box.', 'danger')
            return redirect(url_for('dashboard'))
        try:
            box_name = box.name
            # Delete associated files
            if box.image_path:
                delete_file(box.image_path)
            if box.qr_code_path:
                delete_file(box.qr_code_path)
            db.session.delete(box)
            db.session.commit()
            flash(f'Box "{box_name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting box: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    
    @app.route('/box/<int:box_id>/item/create', methods=['GET', 'POST'])
    @login_required
    def create_item(box_id):
        from forms import ItemForm
        box = Box.query.get_or_404(box_id)
        if box.user_id != current_user.id:
            flash('You do not have permission to add items to this box.', 'danger')
            return redirect(url_for('dashboard'))
        form = ItemForm()
        if form.validate_on_submit():
            try:
                item = Item(
                    name=form.name.data,
                    quantity=form.quantity.data,
                    category=form.category.data,
                    value=form.value.data,
                    notes=form.notes.data,
                    box_id=box.id
                )
                db.session.add(item)
                db.session.commit()
                flash(f'Item "{item.name}" added to box!', 'success')
                return redirect(url_for('view_box', box_id=box.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating item: {str(e)}', 'danger')
        return render_template('itemform.html', form=form, box=box, title='Add Item')
    
    @app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_item(item_id):
        from forms import ItemForm
        item = Item.query.get_or_404(item_id)
        box = item.box
        if box.user_id != current_user.id:
            flash('You do not have permission to edit this item.', 'danger')
            return redirect(url_for('dashboard'))
        form = ItemForm()
        if form.validate_on_submit():
            try:
                item.name = form.name.data
                item.quantity = form.quantity.data
                item.category = form.category.data
                item.value = form.value.data
                item.notes = form.notes.data
                db.session.commit()
                flash(f'Item "{item.name}" updated successfully!', 'success')
                return redirect(url_for('view_box', box_id=box.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating item: {str(e)}', 'danger')
        elif request.method == 'GET':
            form.name.data = item.name
            form.quantity.data = item.quantity
            form.category.data = item.category
            form.value.data = item.value
            form.notes.data = item.notes
        return render_template('itemform.html', form=form, item=item, box=box, title='Edit Item')
    
    @app.route('/item/<int:item_id>/delete', methods=['POST'])
    @login_required
    def delete_item(item_id):
        item = Item.query.get_or_404(item_id)
        box = item.box
        if box.user_id != current_user.id:
            flash('You do not have permission to delete this item.', 'danger')
            return redirect(url_for('dashboard'))
        try:
            item_name = item.name
            db.session.delete(item)
            db.session.commit()
            flash(f'Item "{item_name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting item: {str(e)}', 'danger')
        return redirect(url_for('view_box', box_id=box.id))
    
    @app.route('/scan')
    @login_required
    def scanner():
        return render_template('scanner.html')
    
    @app.route('/qr/<int:box_id>')
    @login_required
    def scan_redirect(box_id):
        box = Box.query.get_or_404(box_id)
        if box.user_id != current_user.id:
            flash('You do not have permission to view this box.', 'danger')
            return redirect(url_for('dashboard'))
        return redirect(url_for('view_box', box_id=box.id))
    
    @app.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        query = request.args.get('q', '').strip()
        category_filter = request.args.get('category', '').strip()
        search_type = request.args.get('type', 'all')
        
        boxes_results = []
        items_results = []
        categories = []
        
        if query:
            if search_type in ['all', 'boxes']:
                boxes_results = Box.query.filter(
                    Box.user_id == current_user.id,
                    (Box.name.ilike(f'%{query}%')) | (Box.location.ilike(f'%{query}%'))
                ).all()
            
            if search_type in ['all', 'items']:
                user_boxes = Box.query.filter_by(user_id=current_user.id).all()
                box_ids = [box.id for box in user_boxes]
                
                if box_ids:
                    items_results = Item.query.filter(
                        Item.box_id.in_(box_ids),
                        (Item.name.ilike(f'%{query}%')) | (Item.category.ilike(f'%{query}%'))
                    ).all()
            
            if category_filter:
                items_results = [item for item in items_results if item.category == category_filter]
        
        user_boxes = Box.query.filter_by(user_id=current_user.id).all()
        box_ids = [box.id for box in user_boxes]
        if box_ids:
            categories = db.session.query(Item.category).filter(
                Item.box_id.in_(box_ids),
                Item.category.isnot(None)
            ).distinct().all()
            categories = [cat[0] for cat in categories]
        
        return render_template(
            'search.html',
            query=query,
            boxes_results=boxes_results,
            items_results=items_results,
            categories=sorted(set(categories)),
            category_filter=category_filter,
            search_type=search_type
        )


# Create the app instance
app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
    
    print("\n🌐 Starting Flask app...")
    print("📍 Open your browser to: http://localhost:8000/")
    print("   or try: http://127.0.0.1:8000/")
    print("   or try: http://0.0.0.0:8000/")
    print("⏹️  Press CTRL+C to stop the server\n")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=8000,
    )