from flask import Flask, render_template, redirect, url_for, flash, request, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
import os
import requests
from datetime import datetime, timedelta

from models import db, User, Product, BlogPost, Project, Order, OrderItem, MaintenanceBooking
from forms import LoginForm, ProductForm # You'll need to update forms.py too

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = 'dev-secret-key-change-this-in-production'
# Database Configuration
db_uri = os.environ.get('NETLIFY_DATABASE_URL')
if db_uri and db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DELIVERY_COST'] = 5000  # Delivery cost in IQD

# Google Auth Config
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId fetch_user info
    client_kwargs={'scope': 'email profile'},
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Utils ---
def admin_required(f):
    def check_admin(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    check_admin.__name__ = f.__name__ # Rename to avoid overwrite errors
    return login_required(check_admin)

def staff_required(f):
    def check_staff(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
            abort(403)
        return f(*args, **kwargs)
    check_staff.__name__ = f.__name__
    return login_required(check_staff)

# --- Routes ---

@app.route('/')
def index():
    # Only fetch simplified categories or specific featured products if needed
    # For now displaying the static homepage
    return render_template('index.html')

@app.route('/calculators')
def calculators():
    return render_template('calculators.html')

@app.route('/products')
def products():
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).order_by(Product.created_at.desc()).all()
    else:
        products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('products.html', products=products, category=category)

@app.route('/offers')
def offers():
    products = Product.query.filter_by(is_special_offer=True).order_by(Product.created_at.desc()).all()
    return render_template('offers.html', products=products)

@app.route('/projects')
def projects():
    # Dynamic projects
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@app.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)

# --- E-commerce Routes ---

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_items = []
    subtotal = 0
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(product_id)
        if product:
            total = product.price * quantity
            subtotal += total
            cart_items.append({'product': product, 'quantity': quantity, 'total': total})
    
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    # Ensure product_id is string key in session json usually, but int key works in python dict
    # Flask session serializes keys to strings sometimes properly
    str_id = str(product_id)
    
    if str_id in cart:
        cart[str_id] += 1
    else:
        cart[str_id] = 1
    
    session.modified = True
    flash('تم إضافة المنتج للسلة', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' not in session:
        return redirect(url_for('cart'))
    
    cart = session['cart']
    str_id = str(product_id)
    
    if str_id in cart:
        del cart[str_id]
        session.modified = True
        flash('تم حذف المنتج من السلة', 'info')
        
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required 
def checkout():
    if not session.get('cart'):
        return redirect(url_for('cart'))

    # Calculate totals again or pass from cart? Better recalculate
    subtotal = 0
    cart_items = []
    for pid, qty in session['cart'].items():
        p = Product.query.get(int(pid))
        if p:
            subtotal += p.price * qty
            cart_items.append({'product': p, 'quantity': qty})
            
    total = subtotal + app.config['DELIVERY_COST']
    
    if request.method == 'POST':
        # Simple form handling without WTForms for speed as requested, or use compact form
        phone = request.form.get('phone')
        address = request.form.get('address')
        date_str = request.form.get('delivery_date')
        
        # Validation
        if not phone or not address or not date_str:
            flash('يرجى ملء كافة الحقول', 'danger')
            return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, total=total, delivery=app.config['DELIVERY_COST'])
            
        delivery_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if delivery_date < datetime.now().date() + timedelta(days=2):
            flash('التاريخ يجب أن يكون بعد يومين على الأقل', 'warning')
            return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, total=total, delivery=app.config['DELIVERY_COST'])

        # Create Order
        delivery_cost = app.config['DELIVERY_COST'] 
        # Total price includes delivery
        order = Order(
            user_id=current_user.id,
            customer_name=current_user.username or 'Customer',
            phone_number=phone,
            address=address,
            delivery_date=delivery_date,
            delivery_cost=delivery_cost,
            total_price=subtotal + delivery_cost, 
            status='New'
        )
        db.session.add(order)
        db.session.commit()
        
        # Add Items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price_at_purchase=item['product'].price
            )
            db.session.add(order_item)
            
        db.session.commit()
        session.pop('cart', None)
        flash('تم استلام طلبك بنجاح!', 'success')
        return redirect(url_for('dashboard')) # Or specific order tracking page
        
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, total=total, delivery=app.config['DELIVERY_COST'])

@app.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        phone_number = request.form.get('phone_number')
        service_type = request.form.get('service_type')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Basic validation
        if not customer_name or not phone_number:
            flash('يرجى ملء الاسم ورقم الهاتف', 'danger')
            return render_template('maintenance_booking.html')
            
        booking = MaintenanceBooking(
            customer_name=customer_name,
            phone_number=phone_number,
            service_type=service_type,
            location_latitude=float(latitude) if latitude else None,
            location_longitude=float(longitude) if longitude else None
        )
        db.session.add(booking)
        db.session.commit()
        
        flash('تم استلام طلب الصيانة. سنتصل بك قريباً.', 'success')
        # Maybe redirect to home or thank you page
        return redirect(url_for('index'))
        
    return render_template('maintenance_booking.html')

# --- Login Route ---
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password_hash and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور', 'danger')
    return render_template('login.html', form=form)

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
    if not user_info.get('email'):
         flash('فشل في جلب البيانات من Google', 'danger')
         return redirect(url_for('login'))

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Create new user
        # Generate a unique username if conflict? For now assume email is enough unique key basis
        username = user_info['email'].split('@')[0]
        # Check if username exists, append rand if so... logic simplified for now
        
        user = User(
            username=username,
            email=user_info['email'],
            google_id=user_info['id'],
            role='customer'
        )
        db.session.add(user)
        db.session.commit()
    elif not user.google_id:
        # Link existing account
        user.google_id = user_info['id']
        db.session.commit()
        
    login_user(user)
    flash('تم تسجيل الدخول بواسطة Google بنجاح!', 'success')
    return redirect(url_for('dashboard')) # Or index

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('index'))

# --- Dashboard & Admin Routes ---

@app.route('/dashboard')
@staff_required
def dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('dashboard.html', products=products)

@app.route('/dashboard/add', methods=['GET', 'POST'])
@staff_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        image_file = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_file = filename
            
        product = Product(
            name=form.name.data, 
            description=form.description.data,
            category=form.category.data,
            image_filename=image_file,
            price=form.price.data, # Expecting form update
            stock=form.stock.data, # Expecting form update
            is_special_offer=form.is_special_offer.data # Expecting form update
        )
        db.session.add(product)
        db.session.commit()
        flash('تم إضافة المنتج بنجاح!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('product_form.html', form=form, title='إضافة منتج')

@app.route('/dashboard/edit/<int:product_id>', methods=['GET', 'POST'])
@staff_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.category = form.category.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.is_special_offer = form.is_special_offer.data
        
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image_filename = filename
            
        db.session.commit()
        flash('تم تحديث المنتج', 'success')
        return redirect(url_for('dashboard'))
    
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.category.data = product.category
        form.price.data = product.price
        form.stock.data = product.stock
        form.is_special_offer.data = product.is_special_offer
        
    return render_template('product_form.html', form=form, title='تعديل المنتج')

@app.route('/dashboard/delete/<int:product_id>')
@staff_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('تم حذف المنتج', 'success')
    return redirect(url_for('dashboard'))

# Application Context Commands
@app.cli.command("create_admin")
def create_admin():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin = User(username='admin', password_hash=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-create admin user
        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(username='admin', password_hash=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created automatically.")
    app.run(debug=True)
