from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'mysecretkeymysecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/') 
    # This is the URL prefix for the auth blueprint, for example: /auth/login
    # app.register_blueprint(auth, url_prefix='/auth') 

    from .models import User
    with app.app_context():
        db.create_all()

        # Add admin user if it doesn't exist
        from .models import User
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

    # Configuracion de LoginManager para evitar acceder a rutas sin estar logueados
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # Si no estamos logueados nos redirigirá a la ruta /login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
