from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required, current_user

# La variable current_user es una variable que se utiliza para saber si un usuario está logueado o no

views = Blueprint('views', __name__)

@views.route('/')
def mainw():
        return render_template("mainw.html")  

@views.route('/home')
@login_required
def home():
    return render_template("home.html", user=current_user) # user=current_user para pasar el usuario a la plantilla home.html y que pueda saber si el usuario está logueado o no

@views.route('/about')
def about():
    return render_template("about.html")

@views.route('/contact')
def contact():
    return render_template("contact.html")
