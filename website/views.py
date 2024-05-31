from flask import Blueprint, json, jsonify, redirect, render_template, url_for, request, flash
from flask_login import login_required, current_user
from .models import db, User, Publication

# La variable current_user es una variable que se utiliza para saber si un usuario está logueado o no

views = Blueprint('views', __name__)

@views.route('/')
def mainw():
        return render_template("mainw.html", user=current_user)  

@views.route('/home')
@login_required
def home():
    return render_template("home.html", user=current_user) # user=current_user para pasar el usuario a la plantilla home.html y que pueda saber si el usuario está logueado o no

@views.route('/about')
def about():
    return render_template("about.html", user=current_user)

@views.route('/contact')
def contact():
    return render_template("contact.html", user=current_user)

@views.route('/profile')
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@views.route('/publications', methods=['GET', 'POST'])
@login_required
def publications():
    if request.method == 'POST':
        publication = request.form.get('publication')

        if len(publication) > 1:
            new_publication = Publication(content=publication, user_id=current_user.id)
            db.session.add(new_publication)
            db.session.commit()
            
            flash('Publication added!', category='success')
            return redirect(url_for('views.publications'))
        else:
            flash('The content must contain at least one character', category='error')
            print('The content must contain at least one character')
        
    return render_template("publications.html", user=current_user)

@views.route('/deletePublication', methods=['POST'])
@login_required
def deletePublication():
    publication = json.loads(request.data)
    publicationId = publication['id']
    publication = Publication.query.get(publicationId)
    if publication:
        if publication.user_id == current_user.id:
            db.session.delete(publication)
            db.session.commit()

    return jsonify({})

@views.route('/viewuser/<email>')
@login_required
def viewuser(email):
    user = User.query.filter_by(email=email).first()
    if user:
        publications = Publication.query.filter_by(user_id=user.id).all()
        return render_template("publications.html", user=user, publications=publications)
    else:
        # Esto hay que cambiarlo
        return "<h1>Usuario no encontrado</h1>"

@views.route('/userlist')
@login_required
def userlist():
    users = User.query.all()
    return render_template("userlist.html", users=users, user=current_user)