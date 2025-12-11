from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Folder, Tracker, Timer, HistoryEvent
from datetime import datetime
import json
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trakstar-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trakstar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- DASHBOARD & FOLDERS ---

@app.route('/dashboard')
@app.route('/folder/<int:folder_id>')
@login_required
def dashboard(folder_id=None):
    current_folder = None
    if folder_id:
        current_folder = Folder.query.get_or_404(folder_id)
        if current_folder.user_id != current_user.id:
            return redirect(url_for('dashboard'))
            
    # Logic to fetch items inside the current folder (or root)
    folders = Folder.query.filter_by(user_id=current_user.id, parent_id=folder_id).all()
    trackers = Tracker.query.filter_by(user_id=current_user.id, folder_id=folder_id).all()
    timers = Timer.query.filter_by(user_id=current_user.id, folder_id=folder_id).all()
    
    # Needed for "Move to Folder" dropdowns
    all_user_folders = Folder.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                         folders=folders, trackers=trackers, timers=timers, 
                         current_folder=current_folder, all_folders=all_user_folders)

# --- CREATION ROUTES ---

@app.route('/create/folder', methods=['POST'])
@login_required
def create_folder():
    name = request.form.get('name')
    color = request.form.get('color')
    parent_id = request.form.get('parent_id') or None # Handle "No Folder" logic
    if parent_id: parent_id = int(parent_id)
    
    new_folder = Folder(name=name, color=color, parent_id=parent_id, owner=current_user)
    db.session.add(new_folder)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/create/tracker', methods=['POST'])
@login_required
def create_tracker():
    name = request.form.get('name')
    color = request.form.get('color')
    parent_id = request.form.get('parent_id') or None
    if parent_id: parent_id = int(parent_id)
    
    new_tracker = Tracker(name=name, color=color, folder_id=parent_id, owner=current_user)
    db.session.add(new_tracker)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/create/timer', methods=['POST'])
@login_required
def create_timer():
    name = request.form.get('name')
    color = request.form.get('color')
    date_str = request.form.get('target_date') # From HTML datetime-local input
    parent_id = request.form.get('parent_id') or None
    if parent_id: parent_id = int(parent_id)
    
    target_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    
    new_timer = Timer(name=name, color=color, target_date=target_date, folder_id=parent_id, owner=current_user)
    db.session.add(new_timer)
    db.session.commit()
    return redirect(request.referrer)

# --- TRACKER ACTIONS ---

@app.route('/tracker/<int:id>/update', methods=['POST'])
@login_required
def update_tracker(id):
    tracker = Tracker.query.get_or_404(id)
    if tracker.owner != current_user: return redirect(url_for('dashboard'))
    
    amount = float(request.form.get('amount'))
    # Log History [cite: 16]
    history = HistoryEvent(amount=amount, tracker_id=tracker.id)
    tracker.value += amount
    
    db.session.add(history)
    db.session.commit()
    return redirect(request.referrer)

# --- DATA EXPORT (Feature ) ---
@app.route('/export')
@login_required
def export_data():
    data = {
        'folders': [{'name': f.name, 'id': f.id} for f in current_user.folders],
        'trackers': [{'name': t.name, 'value': t.value} for t in current_user.trackers],
        'timers': [{'name': tm.name, 'date': str(tm.target_date)} for tm in current_user.timers]
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
