from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
# Para hashear las passwords y solucionar la vulneravilidad de almacenarlas en texto plano en la base de datos
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    print(data)

    return render_template("login.html") 

@auth.route('/sign_up', methods=['GET', 'POST'])
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

        if len(name) < 2:
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

            return redirect(url_for('views.home'))

    return render_template("sign_up.html")

@auth.route('/logout')
def logout():
    return render_template("logout.html")


