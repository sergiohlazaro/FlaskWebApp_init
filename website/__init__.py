# Importación de las librerías necesarias de Flask y otras extensiones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # ORM para interactuar con la base de datos
from flask_login import LoginManager  # Gestión de sesiones y usuarios autenticados
from flask_wtf import CSRFProtect  # Protección contra ataques CSRF (Cross-Site Request Forgery)
import logging  # Para registro de eventos y errores

# Rate Limiting
from flask_limiter import Limiter  # Extensión para limitar la cantidad de solicitudes (protección contra abusos)
from flask_limiter.util import get_remote_address  # Utilidad para obtener la IP del cliente para aplicar el rate limit

# Inicialización del objeto de base de datos SQLAlchemy (se inicializa aquí pero se asociará a la app luego)
db = SQLAlchemy()

# Nombre del archivo de base de datos SQLite que se va a usar
DB_NAME = "database.db"

# Configuración inicial del limitador para limitar por dirección IP (se inicializa aquí pero se asociará a la app luego)
limiter = Limiter(
    get_remote_address  # Cada cliente se identifica por su IP
)

# Función principal que crea y configura la aplicación de Flask
def create_app():
    # Crear la instancia de la aplicación Flask
    app = Flask(__name__)

    # Protección CSRF para formularios
    csrf = CSRFProtect()
    csrf.init_app(app)  # Asocia la protección CSRF a la aplicación

    # Inicialización del limitador de solicitudes (rate limiting)
    limiter.init_app(app)

    # Configuración de la aplicación Flask
    app.config['SECRET_KEY'] = 'mysecretkeymysecretkey'  # Clave secreta para sesiones y cookies
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # URI de conexión a la base de datos SQLite
    app.config['SESSION_COOKIE_SECURE'] = True  # Solo enviar cookies a través de HTTPS (mejora seguridad en producción)
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Las cookies no pueden ser accedidas por JS (previene XSS)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protección contra ataques CSRF entre sitios

    # Asociar la app con la base de datos
    db.init_app(app)

    # Importar los blueprints de vistas y autenticación
    from .views import views
    from .auth import auth

    # Registrar los blueprints para que las rutas definidas estén disponibles
    app.register_blueprint(views, url_prefix='/')  # Todas las rutas en views estarán bajo "/"
    app.register_blueprint(auth, url_prefix='/')   # Todas las rutas en auth estarán bajo "/"

    # Importar el modelo de usuario para inicializar la base de datos con las tablas correctas
    from .models import User

    # Crear las tablas si no existen todavía
    with app.app_context():
        db.create_all()

        # Solo crear usuarios por defecto si no se está en modo TESTING
        if not app.config.get("TESTING"):
            # Comprobar si ya existe un usuario admin
            admin_user = User.query.filter_by(role=0).first()

            # Si no existe un admin, crearlo junto a un usuario regular
            if not admin_user:
                from werkzeug.security import generate_password_hash  # Función para hashear contraseñas

                # Datos del admin
                admin_email = 'admin@admin.com'
                admin_password = 'admin'
                admin_name = 'admin'
                admin_surname = 'admin'
                admin_role = 0  # 0 = rol de admin
                admin_is_blocked = False

                # Crear instancia del usuario administrador
                new_admin = User(name=admin_name,
                                 surname=admin_surname,
                                 email=admin_email,
                                 password=generate_password_hash(admin_password),
                                 role=admin_role,
                                 is_blocked=admin_is_blocked)

                # Añadir y guardar el usuario admin en la base de datos
                db.session.add(new_admin)
                db.session.commit()

                # Datos del usuario regular
                user1_email = 'user1@user.com'
                user1_password = 'password1'
                user1_name = 'User'
                user1_surname = 'One'
                user1_role = 1  # 1 = rol de usuario normal
                user1_is_blocked = False

                # Crear instancia del usuario regular
                new_user1 = User(name=user1_name,
                                 surname=user1_surname,
                                 email=user1_email,
                                 password=generate_password_hash(user1_password),
                                 role=user1_role,
                                 is_blocked=user1_is_blocked)

                # Añadir y guardar el usuario regular en la base de datos
                db.session.add(new_user1)
                db.session.commit()

    # Configuración de la gestión de login (Login Manager)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirigir a esta vista cuando un usuario no autenticado intente acceder a zonas protegidas
    login_manager.init_app(app)  # Asociar la app con el login manager

    # Configuración del logging para registrar eventos en el archivo app.log
    logging.basicConfig(
        filename='app.log',  # Nombre del archivo log
        level=logging.INFO,  # Nivel de severidad mínimo (INFO, se pueden registrar también WARNING, ERROR...)
        format='%(asctime)s [%(levelname)s] %(message)s'  # Formato de cada entrada de log
    )

    # Función que Flask-Login usa para cargar un usuario desde su ID almacenado en la sesión
    @login_manager.user_loader
    def load_user(id):
        # Devuelve la instancia del usuario correspondiente a la ID
        return User.query.get(int(id))

    # Devuelve la aplicación ya configurada
    return app
