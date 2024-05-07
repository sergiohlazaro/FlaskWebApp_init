from flask import Blueprint, render_template, request, flash

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
        nickname = request.form.get('nickname') 
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        print(name, surname, nickname, email, password, password2)

        if len(name) < 2:
            print('First name must be at least 2 characters long.')
        elif len(surname) < 2:
            print('Last name must be at least 2 characters long.')
        elif len(nickname) < 2:
            print('Nickname must be at least 2 characters long.')
        elif password != password2:
            print('Passwords do not match.')
        elif len(password) < 8:
            print('Password must be at least 8 characters long.')
        else:
            # Add user to database
            print('Sign up successful.')

    return render_template("sign_up.html")

@auth.route('/logout')
def logout():
    return render_template("logout.html")


