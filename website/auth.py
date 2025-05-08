# Importación de librerías de Flask necesarias para el manejo de rutas, renderizado de plantillas y gestión de peticiones
from flask import Blueprint, render_template, request, flash, redirect, url_for

# Importación de los modelos de base de datos
from .models import LoginRecord, User

# Importación de la instancia de la base de datos
from . import db

# Importación de funciones para gestión de usuarios autenticados
from flask_login import login_user, login_required, logout_user, current_user

# Importación de utilidades para hashear (encriptar) contraseñas
from werkzeug.security import generate_password_hash, check_password_hash

# Importación del limitador de solicitudes (Rate Limiting) para prevenir ataques de fuerza bruta
from . import limiter

from flask import session

import time

# Creación de un Blueprint llamado 'auth' para agrupar todas las rutas relacionadas con autenticación
auth = Blueprint('auth', __name__)

# Estructura para almacenar intentos fallidos → en memoria por IP
FAILED_LOGINS = {}

# Configuración del bloqueo temporal
MAX_FAILED_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 600  # 10 minutos bloqueado tras superar el límite

# -----------------------
# LOGIN
# -----------------------

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")  # Limite global por IP
def login():
    # Obtiene la IP del cliente
    ip_address = request.remote_addr

    # Verificar si la IP está bloqueada
    block_info = FAILED_LOGINS.get(ip_address)
    if block_info:
        failed_attempts, last_attempt_time = block_info

        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            # Si está dentro del tiempo de bloqueo, rechazar
            if time.time() - last_attempt_time < BLOCK_TIME_SECONDS:
                flash("Too many failed login attempts. Try again later.", category='error')
                return render_template("login.html", user=current_user)
            else:
                # Si pasó el tiempo de bloqueo, resetear intentos
                FAILED_LOGINS[ip_address] = [0, 0]

    # Procesar formulario de login
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # Usuario no existe
        if not user:
            flash('Email does not exist', category='error')
            # Registrar intento fallido
            FAILED_LOGINS[ip_address] = [FAILED_LOGINS.get(ip_address, [0, 0])[0] + 1, time.time()]

        # Usuario bloqueado
        elif user.is_blocked:
            flash('This account has been blocked', category='error')

        # Usuario existe y no está bloqueado
        else:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')

                # Iniciar sesión
                login_user(user, remember=True)

                # Registrar IP en LoginRecord
                login_record = LoginRecord(user_id=user.id, ip_address=ip_address)
                db.session.add(login_record)
                db.session.commit()

                # Reiniciar contador de fallos en caso de éxito
                FAILED_LOGINS[ip_address] = [0, 0]

                return redirect(url_for('views.home'))

            else:
                flash('Incorrect password, try again', category='error')
                # Registrar intento fallido
                FAILED_LOGINS[ip_address] = [FAILED_LOGINS.get(ip_address, [0, 0])[0] + 1, time.time()]

    return render_template("login.html", user=current_user)

# -----------------------
# SIGN UP (Registro)
# -----------------------

@auth.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def sign_up():
    # Capturar datos del formulario
    data = request.form

    if request.method == 'POST':
        # Recoger los campos del formulario
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Validación de datos

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', category='error')

        elif len(name) < 2:
            flash('First name must be at least 2 characters long', category='error')

        elif len(surname) < 2:
            flash('Last name must be at least 2 characters long', category='error')

        elif password != password2:
            flash('Passwords do not match.', category='error')

        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')

        else:
            # Crear el usuario
            new_user = User(
                name=name,
                surname=surname,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256')
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully', category='success')

            # Iniciar sesión
            login_user(new_user, remember=True)

            # Registrar IP
            ip_address = request.remote_addr
            login_record = LoginRecord(user_id=new_user.id, ip_address=ip_address)
            db.session.add(login_record)
            db.session.commit()

            return render_template("home.html", user=current_user)

    return render_template("sign_up.html", user=current_user)

# -----------------------
# LOGOUT
# -----------------------

@auth.route('/logout')
@login_required  # Solo usuarios autenticados pueden hacer logout
def logout():
    # Cierra la sesión del usuario actual
    logout_user()

    # Redirige al login
    return redirect(url_for('auth.login'))
