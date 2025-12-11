from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Expense
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
# Use SQLite for local, but allow environment variable for Cloud (Render/VerceL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create DB on first run
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        
        # Hashing password for security (Requirement)
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Check username and password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch User Data (CRUD - Read)
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    
    # Prepare Data for Chart.js (Data Processing)
    categories = {}
    for expense in expenses:
        if expense.category in categories:
            categories[expense.category] += expense.amount
        else:
            categories[expense.category] = expense.amount
            
    return render_template('dashboard.html', expenses=expenses, chart_data=categories)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        category = request.form.get('category')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        new_expense = Expense(category=category, amount=amount, description=description, author=current_user)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

@app.route('/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
