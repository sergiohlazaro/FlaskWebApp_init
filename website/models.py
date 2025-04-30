from datetime import datetime
import pytz
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# Definición del modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    surname = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, default="This is my bio.")  # Bio field
    role = db.Column(db.Integer, nullable=False, default=1)  # 0 para admin, 1 para usuario regular
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)  # Campo para indicar si el usuario está bloqueado
    profile_pic = db.Column(db.String(150), default='default.jpg')
    twitter = db.Column(db.String(255), nullable=True)    # Twitter URL
    linkedin = db.Column(db.String(255), nullable=True)   # LinkedIn URL
    publications = db.relationship('Publication')
    login_records = db.relationship('LoginRecord')

# Definicion del modelo de publicaciones
class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)

# Definicion del modelo de registro de login
class LoginRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Madrid')))

# Definicion del modelo de mensajes
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    file_path = db.Column(db.String(255), nullable=True)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


