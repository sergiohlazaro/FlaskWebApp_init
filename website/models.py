from datetime import datetime
import pytz
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# Definición del modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    surname = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=1)  # 0 para admin, 1 para usuario regular
    publications = db.relationship('Publication')
    login_records = db.relationship('LoginRecord')

# Definicion del modelo de publicaciones
class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Definicion del modelo de registro de login
class LoginRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Madrid')))

