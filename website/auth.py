from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import LoginRecord, User
from . import db
from flask_login import login_user, login_required, logout_user, current_user
# Para hashear las passwords y solucionar la vulneravilidad de almacenarlas en texto plano en la base de datos
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    print(data)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email does not exist', category='error')
            print('Email does not exist')
        elif user.is_blocked:
            flash('This account has been blocked', category='error')
            print('This account has been blocked')
        else:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')
                print('Logged in successfully')
                login_user(user, remember=True) # remember=True para que se mantenga la sesion iniciada (vuln cookies)
                
                # Guardar la dirección IP del usuario
                ip_address = request.remote_addr
                login_record = LoginRecord(user_id=user.id, ip_address=ip_address)
                db.session.add(login_record)
                db.session.commit()
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again', category='error')
                print('Incorrect password, try again') 

    return render_template("login.html", user=current_user) # user=current_user para pasar el usuario a la plantilla login.html y que pueda saber si el usuario está logueado o no 

@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    data = request.form
    print(data)

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        print(name, surname, email, password, password2)

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', category='error')
            print('Email already exists')
        elif len(name) < 2:
            flash('First name must be at least 2 characters long', category='error')
            print('First name must be at least 2 characters long')
        elif len(surname) < 2:
            flash('Last name must be at least 2 characters long', category='error')
            print('Last name must be at least 2 characters long')
        elif password != password2:
            flash('Passwords do not match.', category='error')
            print('Passwords do not match.')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')
            print('Password must be at least 8 characters long')
        else:
            # Add user to database:
            new_user = User(name=name, surname=surname, email=email, password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfuly', category='success')
            print('Sign up successful')
            login_user(new_user, remember=True) # remember=True para que se mantenga la sesion iniciada (vuln cookies)
            
            # Guardar la dirección IP del usuario
            ip_address = request.remote_addr
            login_record = LoginRecord(user_id=new_user.id, ip_address=ip_address)
            db.session.add(login_record)
            db.session.commit()
            return redirect(url_for('views.home'))
        
    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


