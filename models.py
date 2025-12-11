from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False) # Changed from username to email per PDF
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Relationships
    folders = db.relationship('Folder', backref='owner', lazy=True)
    trackers = db.relationship('Tracker', backref='owner', lazy=True)
    timers = db.relationship('Timer', backref='owner', lazy=True)

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default="#0d6efd") # User-defined UI colors [cite: 29]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True) # Nested organization 
    
    # Self-referential relationship for subfolders
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy=True)
    trackers = db.relationship('Tracker', backref='folder', lazy=True)
    timers = db.relationship('Timer', backref='folder', lazy=True)

class Tracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, default=0.0)
    color = db.Column(db.String(20), default="#198754")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    
    # Transaction History [cite: 16]
    history = db.relationship('HistoryEvent', backref='tracker', cascade="all, delete-orphan", lazy=True)

class HistoryEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    tracker_id = db.Column(db.Integer, db.ForeignKey('tracker.id'), nullable=False)

class Timer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_date = db.Column(db.DateTime, nullable=False) # For specific dates 
    color = db.Column(db.String(20), default="#dc3545")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
