# ----------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS Y EXTENSIONES
# ----------------------------------------------

from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # ORM para la base de datos
from flask_login import LoginManager  # Gestión de sesiones de usuario
from flask_wtf import CSRFProtect  # Protección contra ataques CSRF
from flask_limiter import Limiter  # Límite de solicitudes (Rate Limiting)
from flask_limiter.util import get_remote_address  # Obtención de IP del cliente
from flask_caching import Cache  # Sistema de cache para mejorar rendimiento
import logging  # Registro de eventos y errores
from flask_compress import Compress

# ----------------------------------------------
# INSTANCIAS GLOBALES DE EXTENSIONES
# ----------------------------------------------

# ORM para la base de datos
db = SQLAlchemy()

# Rate limiter basado en IP
limiter = Limiter(get_remote_address)

# Cache en memoria simple (se puede cambiar a redis, filesystem...)
cache = Cache()

# Nombre del archivo de base de datos SQLite
DB_NAME = "database.db"

# ----------------------------------------------
# CREACIÓN Y CONFIGURACIÓN DE LA APLICACIÓN
# ----------------------------------------------

def create_app():
    # Crear la instancia de Flask
    app = Flask(__name__)

    Compress(app)

    # ------------------------------
    # CONFIGURACIÓN DE LA APP
    # ------------------------------

    app.config['SECRET_KEY'] = 'mysecretkeymysecretkey'  # Protección de sesiones y cookies
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # Base de datos SQLite
    app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024  # Límite máximo de archivos subidos (24MB)

    # Seguridad en cookies
    app.config['SESSION_COOKIE_SECURE'] = True      # Solo enviar por HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True    # Inaccesibles vía Javascript (mitiga XSS)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # Previene ataques CSRF entre sitios

    # ------------------------------
    # INICIALIZACIÓN DE EXTENSIONES
    # ------------------------------

    # Protección CSRF
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Inicializar Rate Limiting
    limiter.init_app(app)

    # Inicializar Cache
    cache.init_app(app)

    # Inicializar Base de Datos
    db.init_app(app)

    # ------------------------------
    # REGISTRO DE BLUEPRINTS
    # ------------------------------

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # ------------------------------
    # CREACIÓN DE TABLAS Y USUARIOS POR DEFECTO
    # ------------------------------

    from .models import User

    with app.app_context():
        db.create_all()

        if not app.config.get("TESTING"):
            admin_user = User.query.filter_by(role=0).first()

            if not admin_user:
                from werkzeug.security import generate_password_hash

                # Crear usuario administrador
                new_admin = User(
                    name='admin',
                    surname='admin',
                    email='admin@admin.com',
                    password=generate_password_hash('admin'),
                    role=0,
                    is_blocked=False
                )
                db.session.add(new_admin)

                # Crear usuario normal
                new_user1 = User(
                    name='User',
                    surname='One',
                    email='user1@user.com',
                    password=generate_password_hash('password1'),
                    role=1,
                    is_blocked=False
                )
                db.session.add(new_user1)

                db.session.commit()

    # ------------------------------
    # LOGIN MANAGER (gestión de sesiones)
    # ------------------------------

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # ------------------------------
    # CONFIGURACIÓN DE LOGGING
    # ------------------------------

    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # ------------------------------
    # DEVOLVER APLICACIÓN CONFIGURADA
    # ------------------------------
    return app
