import os
from werkzeug.utils import secure_filename
from flask import Blueprint, json, jsonify, redirect, render_template, url_for, request, flash, request
from flask_login import login_required, current_user
from .models import db, LoginRecord, User, Publication, Message
from werkzeug.security import check_password_hash, generate_password_hash

# La variable current_user es una variable que se utiliza para saber si un usuario está logueado o no

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'website/static/profile_pics'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        confirm_email = request.form.get('confirm_email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Actualización de email
        if new_email and confirm_email:
            if new_email != confirm_email:
                flash('Emails do not match', category='error')
                print('Emails do not match')
                return render_template('profile.html', user=current_user)
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                flash('Email already exists', category='error')
                print('Email already exists')
                return render_template('profile.html', user=current_user)
            else:
                current_user.email = new_email

        # Actualización de contraseña
        if current_password and new_password and confirm_password:
            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect', category='error')
                print('Current password is incorrect')
                return render_template('profile.html', user=current_user)
            if len(new_password) < 8:
                flash('New password must be at least 8 characters long', category='error')
                print('New password must be at least 8 characters long')
                return render_template('profile.html', user=current_user)
            if new_password != confirm_password:
                flash('New passwords do not match', category='error')
                print('New passwords do not match')
                return render_template('profile.html', user=current_user)
            else:
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

        # Subida de imagen de perfil
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename == '':
                flash('No selected file', category='error')
                return render_template('profile.html', user=current_user)
            if file and allowed_file(file.filename):
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                current_user.profile_pic = filename

        db.session.commit()
        flash('Profile updated', category='success')
        print('Profile updated')

    return render_template('profile.html', user=current_user)

@views.route('/admin')
@login_required
def admin():
    if current_user.role != 0:
        flash('You are not allowed to access this page', category='error')
        print('You are not allowed to access this page')
        return redirect(url_for('views.home'))
    
    users = User.query.all()
    login_records = LoginRecord.query.all()
    return render_template('admin.html', user=current_user, users=users, login_records=login_records)

@views.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_blocked = True
        db.session.commit()
        flash('User blocked', category='success')
    else:
        flash('User not found', category='error')
    return redirect(url_for('views.admin'))

@views.route('/unblock_user/<user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_blocked = False
        db.session.commit()
        flash('User has been unblocked', category='success')
    else:
        flash('User does not exist', category='error')
    return redirect(url_for('views.admin'))

@views.route('/publications', methods=['GET', 'POST'])
@login_required
def publications():
    if request.method == 'POST':
        publication = request.form.get('publication')

        if len(publication) > 1:
            new_publication = Publication(content=publication, user_id=current_user.id)
            db.session.add(new_publication)
            db.session.commit()
            
            flash('Publication added', category='success')
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
            return render_template("publications.html", user=current_user)
    else:
        flash('Publication not found', category='error')
        print('Publication not found')
        return render_template("publications.html", user=current_user)

@views.route('/viewuser/<email>')
@login_required
def viewuser(email):
    user = User.query.filter_by(email=email).first()
    if user:
        publications = Publication.query.filter_by(user_id=user.id).all()
        return render_template("publications.html", user=user, publications=publications)
    else:
        flash('User not found', category='error')
        print('User not found')
        return render_template("userlist.html", user=current_user)

@views.route('/userlist')
@login_required
def userlist():
    users = User.query.all()
    return render_template("userlist.html", users=users, user=current_user)

@views.route('/messages', methods=['GET'])
@login_required
def messages():
    # Users the current user has communicated with
    users_contacted = db.session.query(User).join(
        Message, (Message.sender_id == User.id) | (Message.receiver_id == User.id)
    ).filter(User.id != current_user.id).distinct().all()

    selected_user_id = request.args.get('user_id', type=int)
    conversation = None

    if selected_user_id:
        # Get conversation with the selected user
        conversation = Message.query.filter(
            (Message.sender_id == current_user.id) & (Message.receiver_id == selected_user_id) |
            (Message.receiver_id == current_user.id) & (Message.sender_id == selected_user_id)
        ).order_by(Message.timestamp).all()

    return render_template(
        'messages.html',
        user=current_user,
        users_contacted=users_contacted,
        conversation=conversation,
        selected_user_id=selected_user_id
    )

@views.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver_email = request.form.get('receiver_email')
    content = request.form.get('content')

    if not receiver_email or not content:
        flash('Receiver email and content are required!', category='error')
        return redirect(url_for('views.messages'))

    receiver = User.query.filter_by(email=receiver_email).first()
    if not receiver:
        flash('User with this email does not exist!', category='error')
        return redirect(url_for('views.messages'))

    new_message = Message(sender_id=current_user.id, receiver_id=receiver.id, content=content)
    db.session.add(new_message)
    db.session.commit()
    flash('Message sent!', category='success')
    return redirect(url_for('views.messages'))

@views.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    original_message = Message.query.get_or_404(message_id)
    content = request.form.get('content')
    if not content:
        flash('Reply content is required!', category='error')
        return redirect(url_for('views.messages'))

    reply_message = Message(sender_id=current_user.id, receiver_id=original_message.sender_id, content=content)
    db.session.add(reply_message)
    db.session.commit()
    flash('Reply sent!', category='success')
    return redirect(url_for('views.messages'))

