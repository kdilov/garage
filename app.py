# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User, Box, Item
from forms import RegistrationForm, LoginForm
import os
import sys
import traceback
import qrcode
import io
from base64 import b64encode


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize extensions with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


def generate_qr_code(box_id, box_name):
    """
    Generate a QR code for a box and return the file path.
    The QR code contains a URL to scan the box.
    """
    try:
        # Use relative path or IP-friendly URL
        # This URL should work on local network
        # When scanned on phone, it will go to /qr/<box_id> which redirects to view_box
        box_url = f"/qr/{box_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(box_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to static/qrcodes folder
        import os
        qr_dir = 'static/qrcodes'
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
        
        # Save with box ID as filename
        filename = f"{qr_dir}/box_{box_id}.png"
        img.save(filename)
        
        return filename
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """
    This callback is used to reload the user object from the user ID stored in the session.
    """
    return User.query.get(int(user_id))


# Home route
@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page - shows different content for logged in vs logged out users"""
    if request.method == 'POST':
        print("POST request received:", request.form)
    return render_template('index.html')


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        flash('You are already registered and logged in!', 'info')
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        flash(f'Account created successfully for {user.username}! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to the page they were trying to access, or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('login.html', form=form)


# Logout route
@app.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


# Dashboard route (protected)
@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - shows all user's boxes"""
    boxes = Box.query.filter_by(user_id=current_user.id).all()
    return render_template('boxlist.html', boxes=boxes)

# Create box route
@app.route('/box/create', methods=['GET', 'POST'])
@login_required
def create_box():
    """Create a new storage box"""
    from forms import BoxForm
    
    form = BoxForm()
    
    if form.validate_on_submit():
        try:
            # Create new box
            box = Box(
                name=form.name.data,
                location=form.location.data,
                description=form.description.data,
                user_id=current_user.id
            )
            
            # Add to database first to get the ID
            db.session.add(box)
            db.session.flush()
            
            # Generate QR code with the box ID
            qr_path = generate_qr_code(box.id, box.name)
            box.qr_code_path = qr_path
            
            # Commit the changes
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
    """View a single box and its items"""
    box = Box.query.get_or_404(box_id)
    if box.user_id != current_user.id:
        flash('You do not have permission to view this box.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('boxdetail.html', box=box)


@app.route('/box/<int:box_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_box(box_id):
    """Edit an existing box"""
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
    """Delete a box"""
    box = Box.query.get_or_404(box_id)
    if box.user_id != current_user.id:
        flash('You do not have permission to delete this box.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        box_name = box.name
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
    """Create a new item in a box"""
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
    """Edit an existing item"""
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
    """Delete an item"""
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

# QR Scanner route
@app.route('/scan')
@login_required
def scanner():
    """QR code scanner page - uses phone camera to scan boxes"""
    return render_template('scanner.html')


# QR Redirect route (called when QR is scanned)
@app.route('/qr/<int:box_id>')
@login_required
def scan_redirect(box_id):
    """Handle scanned QR codes - redirect to box detail"""
    box = Box.query.get_or_404(box_id)
    
    # Check if user owns this box
    if box.user_id != current_user.id:
        flash('You do not have permission to view this box.', 'danger')
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('view_box', box_id=box.id))


# Search route
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Search boxes and items"""
    query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_type = request.args.get('type', 'all')  # all, boxes, items
    
    boxes_results = []
    items_results = []
    categories = []
    
    if query:
        # Search boxes
        if search_type in ['all', 'boxes']:
            boxes_results = Box.query.filter(
                Box.user_id == current_user.id,
                (Box.name.ilike(f'%{query}%')) | (Box.location.ilike(f'%{query}%'))
            ).all()
        
        # Search items
        if search_type in ['all', 'items']:
            # Get all user's boxes first
            user_boxes = Box.query.filter_by(user_id=current_user.id).all()
            box_ids = [box.id for box in user_boxes]
            
            if box_ids:
                items_results = Item.query.filter(
                    Item.box_id.in_(box_ids),
                    (Item.name.ilike(f'%{query}%')) | (Item.category.ilike(f'%{query}%'))
                ).all()
        
        # Apply category filter if provided
        if category_filter:
            items_results = [item for item in items_results if item.category == category_filter]
    
    # Get all categories for filter dropdown
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



if __name__ == '__main__':
    try:
        # Create application context and initialize database
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully!")
        
        # Run the development server
        print("\n🌐 Starting Flask app...")
        print("📍 Open your browser to: http://localhost:8000/")
        print("   or try: http://127.0.0.1:8000/")
        print("   or try: http://0.0.0.0:8000/")
        print("⏹️  Press CTRL+C to stop the server\n")
        
        app.run(
            debug=True,  # Disable debug mode temporarily
            host='0.0.0.0',  # Listen on all interfaces
            port=8000,
            
            

        )
    except Exception as e:
        print(f"❌ Error starting Flask app:")
        import traceback
        print(traceback.format_exc())
