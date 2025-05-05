# Importar módulo para trabajar con fechas y horas
from datetime import datetime
import pytz  # Biblioteca para manejo de zonas horarias

# Importar la instancia de SQLAlchemy de la aplicación
from . import db

# UserMixin proporciona métodos útiles para usuarios autenticados (Flask-Login)
from flask_login import UserMixin

# Función de SQLAlchemy para obtener el timestamp del momento en el que se crea un registro
from sqlalchemy.sql import func

# -----------------------
# MODELO DE USUARIOS
# -----------------------

class User(UserMixin, db.Model):
    # Declaración de tabla → automáticamente será "user" en la base de datos

    # ID único del usuario (clave primaria)
    id = db.Column(db.Integer, primary_key=True)

    # Nombre del usuario
    name = db.Column(db.String(100), unique=False, nullable=False)

    # Apellido del usuario
    surname = db.Column(db.String(100), unique=False, nullable=False)

    # Email del usuario (debe ser único para evitar registros duplicados)
    email = db.Column(db.String(100), unique=True, nullable=False)

    # Contraseña hasheada del usuario (almacenada de manera segura)
    password = db.Column(db.String(100), nullable=False)

    # Biografía del usuario (texto largo opcional). Tiene un valor por defecto
    bio = db.Column(db.Text, default="This is my bio.")

    # Rol del usuario: 0 = administrador, 1 = usuario normal
    role = db.Column(db.Integer, nullable=False, default=1)

    # Estado de bloqueo de la cuenta (True = bloqueado, False = activo)
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)

    # Imagen de perfil (cadena con el nombre del archivo)
    profile_pic = db.Column(db.String(150), default='default.jpg')

    # Campo para URL del perfil de Twitter (opcional)
    twitter = db.Column(db.String(255), nullable=True)

    # Campo para URL del perfil de LinkedIn (opcional)
    linkedin = db.Column(db.String(255), nullable=True)

    # Relación uno a muchos con publicaciones → Un usuario puede tener muchas publicaciones
    publications = db.relationship('Publication')

    # Relación uno a muchos con registros de inicio de sesión → Un usuario puede tener múltiples registros de login
    login_records = db.relationship('LoginRecord')

# -----------------------
# MODELO DE PUBLICACIONES
# -----------------------

class Publication(db.Model):
    # ID único de la publicación
    id = db.Column(db.Integer, primary_key=True)

    # Contenido de la publicación (campo obligatorio)
    content = db.Column(db.Text, nullable=False)

    # Fecha de publicación → Se almacena con timezone. Por defecto, la fecha actual
    date = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relación con el usuario → Clave foránea
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Ruta de archivo opcional (se puede adjuntar un archivo a la publicación)
    file_path = db.Column(db.String(255), nullable=True)

# -----------------------
# MODELO DE REGISTRO DE LOGIN
# -----------------------

class LoginRecord(db.Model):
    # ID único del registro de login
    id = db.Column(db.Integer, primary_key=True)

    # Relación con el usuario → Clave foránea
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Dirección IP desde donde se hizo login → Muy útil para seguridad
    ip_address = db.Column(db.String(50), nullable=False)

    # Fecha y hora del login → Por defecto se establece a la hora local de Madrid (zona horaria definida con pytz)
    login_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Madrid')))

# -----------------------
# MODELO DE MENSAJES
# -----------------------

class Message(db.Model):
    # ID único del mensaje
    id = db.Column(db.Integer, primary_key=True)

    # ID del remitente del mensaje (clave foránea relacionada con el usuario)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ID del receptor del mensaje (clave foránea relacionada con el usuario)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Contenido del mensaje
    content = db.Column(db.Text, nullable=False)

    # Timestamp de cuándo se envió el mensaje → Por defecto se establece al momento actual
    timestamp = db.Column(db.DateTime, default=func.now())

    # Ruta opcional a un archivo adjunto
    file_path = db.Column(db.String(255), nullable=True)

    # Relaciones para facilitar el acceso a datos relacionados
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

