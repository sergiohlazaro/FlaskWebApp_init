from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager
from flask_wtf import CSRFProtect
import logging

# Rate Limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
DB_NAME = "database.db"

limiter = Limiter(
    get_remote_address
)


def create_app():
    app = Flask(__name__)

    csrf = CSRFProtect()
    csrf.init_app(app)

    limiter.init_app(app)  # Inicialización del rate limiting

    app.config['SECRET_KEY'] = 'mysecretkeymysecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SESSION_COOKIE_SECURE'] = True  # Solo en producción con HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/') 

    from .models import User
    with app.app_context():
        db.create_all()

        # Añadir admin por defecto si no existe
        admin_user = User.query.filter_by(role=0).first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_email = 'admin@admin.com'
            admin_password = 'admin'
            admin_name = 'admin'
            admin_surname = 'admin'
            admin_role = 0
            admin_is_blocked = False
            
            new_admin = User(name=admin_name,
                             surname=admin_surname,
                             email=admin_email,
                             password=generate_password_hash(admin_password),
                             role=admin_role,
                             is_blocked=admin_is_blocked)
            db.session.add(new_admin)
            db.session.commit()

            user1_email = 'user1@user.com'
            user1_password = 'password1'
            user1_name = 'User'
            user1_surname = 'One'
            user1_role = 1
            user1_is_blocked = False
            
            new_user1 = User(name=user1_name,
                             surname=user1_surname,
                             email=user1_email,
                             password=generate_password_hash(user1_password),
                             role=user1_role,
                             is_blocked=user1_is_blocked)
            db.session.add(new_user1)
            db.session.commit()

    # Configuración de login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
