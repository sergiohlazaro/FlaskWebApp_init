from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

views = Blueprint('views', __name__)

@views.route('/')
def mainw():
        return render_template("mainw.html")  

@views.route('/home')
def home():
    return render_template("home.html")

@views.route('/about')
def about():
    return render_template("about.html")

@views.route('/contact')
def contact():
    return render_template("contact.html")
