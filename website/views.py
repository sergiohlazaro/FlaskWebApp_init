# ---------------------------------
# IMPORTACIONES
# ---------------------------------
import os  # Librería para operaciones con archivos y carpetas
from werkzeug.utils import secure_filename  # Asegura que los nombres de archivos sean seguros para guardarlos
from flask import Blueprint, json, jsonify, redirect, render_template, url_for, request, flash
from flask_login import login_required, current_user, logout_user  # Gestión de sesiones de usuarios

# Modelos de base de datos
from .models import db, LoginRecord, User, Publication, Message

# Para hashear y verificar contraseñas
from werkzeug.security import check_password_hash, generate_password_hash

# Consultas avanzadas de SQLAlchemy
from sqlalchemy import or_, and_

# Sanitización de entradas para evitar ataques XSS
import bleach

# Para verificar tipo real de archivos subidos
import imghdr

# Para logging de eventos
import logging

# Para procesamiento de imágenes
from PIL import Image

# ---------------------------------
# CONFIGURACIONES
# ---------------------------------

# Creación del blueprint para agrupar todas las rutas de "views"
views = Blueprint('views', __name__)

# Extensiones permitidas para imágenes de perfil
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Extensiones permitidas para archivos de publicaciones/mensajes
ALLOWED_EXTENSIONS_DOCS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

# Carpeta donde se guardarán las imágenes de perfil
UPLOAD_FOLDER = 'website/static/profile_pics'

# ---------------------------------
# FUNCIONES DE UTILIDAD
# ---------------------------------

# Verifica si un archivo tiene una extensión válida para imágenes
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Verifica si un archivo tiene una extensión válida para archivos en general
def allowed_file_generic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_DOCS

# ---------------------------------
# RUTAS PRINCIPALES (HOME, ABOUT, CONTACT)
# ---------------------------------

@views.route('/')
def mainw():
    return render_template("mainw.html", user=current_user)

@views.route('/home')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/about')
def about():
    return render_template("about.html", user=current_user)

@views.route('/contact')
def contact():
    return render_template("contact.html", user=current_user)

# ---------------------------------
# PERFIL DE USUARIO (EDITAR PERFIL)
# ---------------------------------

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Permite a los usuarios actualizar su email, contraseña y foto de perfil.
    """
    if request.method == 'POST':
        # --- Actualización de email ---
        new_email_raw = request.form.get('new_email')
        confirm_email_raw = request.form.get('confirm_email')

        new_email = bleach.clean(new_email_raw) if new_email_raw else ''
        confirm_email = bleach.clean(confirm_email_raw) if confirm_email_raw else ''

        if new_email and confirm_email:
            if new_email != confirm_email:
                flash('Emails do not match', category='error')
                return render_template('profile.html', user=current_user)

            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                flash('Email already exists', category='error')
                return render_template('profile.html', user=current_user)
            else:
                current_user.email = new_email
                logging.info(f"User {current_user.id} updated email to {new_email}")

        # --- Actualización de contraseña ---
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password and new_password and confirm_password:
            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect', category='error')
                return render_template('profile.html', user=current_user)
            if len(new_password) < 8:
                flash('New password must be at least 8 characters long', category='error')
                return render_template('profile.html', user=current_user)
            if new_password != confirm_password:
                flash('New passwords do not match', category='error')
                return render_template('profile.html', user=current_user)
            else:
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                logging.info(f"User {current_user.id} updated password.")

        # --- Subida de imagen de perfil ---
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename == '':
                flash('No selected file', category='error')
                return render_template('profile.html', user=current_user)
            if file and allowed_file(file.filename):
                file_bytes = file.read()
                file.seek(0)
                detected_type = imghdr.what(None, h=file_bytes)
                if detected_type in ALLOWED_EXTENSIONS:
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    image = Image.open(file)
                    image.thumbnail((300, 300))  # Redimensionar a máximo 300x300
                    image.save(filepath)

                    current_user.profile_pic = filename
                else:
                    flash('Invalid image file type.', category='error')
                    return render_template('profile.html', user=current_user)

        db.session.commit()
        flash('Profile updated successfully.', category='success')

    return render_template('profile.html', user=current_user)

# ---------------------------------
# ACTUALIZAR BIOGRAFÍA
# ---------------------------------

@views.route('/update_bio', methods=['POST'])
@login_required
def update_bio():
    bio_raw = request.form.get('bio')
    bio = bleach.clean(bio_raw)
    if len(bio) > 100:
        flash('Bio too long. Maximum 100 characters.', category='error')
    else:
        current_user.bio = bio
        db.session.commit()
        flash('Your bio has been updated.', category='success')
    return render_template('profile.html', user=current_user)

# ---------------------------------
# ACTUALIZAR REDES SOCIALES
# ---------------------------------

@views.route('/update_social_links', methods=['POST'])
@login_required
def update_social_links():
    twitter = request.form.get('twitter')
    linkedin = request.form.get('linkedin')
    current_user.twitter = bleach.clean(twitter)
    current_user.linkedin = bleach.clean(linkedin)
    db.session.commit()
    flash('Social media links updated.', category='success')
    return render_template('profile.html', user=current_user)

# ---------------------------------
# ELIMINAR CUENTA
# ---------------------------------

@views.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    Elimina el usuario actual y todos sus datos relacionados (mensajes, publicaciones, registros de login).
    """
    user_id = current_user.id

    # Borrar publicaciones
    Publication.query.filter_by(user_id=user_id).delete()

    # Borrar mensajes enviados o recibidos
    Message.query.filter((Message.sender_id == user_id) | (Message.receiver_id == user_id)).delete()

    # Borrar registros de login
    LoginRecord.query.filter_by(user_id=user_id).delete()

    # Borrar el propio usuario
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash('Your account has been deleted.', category='success')
    return redirect(url_for('auth.login'))

# ---------------------------------
# PANEL DE ADMINISTRACIÓN
# ---------------------------------

@views.route('/admin')
@login_required
def admin():
    """
    Solo accesible para administradores.
    Muestra la lista de usuarios (excepto uno mismo) y sus registros de inicio de sesión.
    """

    # Verificar que el usuario tiene rol de administrador
    if current_user.role != 0:
        flash('You are not allowed to access this page', category='error')
        print('Access denied - User is not admin')
        return redirect(url_for('views.home'))

    # Obtener todos los usuarios excepto el admin que está logueado
    users = User.query.filter(User.id != current_user.id).all()

    # Obtener todos los registros de inicio de sesión
    login_records = LoginRecord.query.all()

    # Renderizar panel de administración
    return render_template('admin.html', user=current_user, users=users, login_records=login_records)

# ---------------------------------
# BLOQUEAR Y DESBLOQUEAR USUARIOS (Solo Admin)
# ---------------------------------

@views.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    """
    Bloquea a un usuario (solo accesible para admins desde el panel).
    """
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
    """
    Desbloquea a un usuario previamente bloqueado.
    """
    user = User.query.get(user_id)
    if user:
        user.is_blocked = False
        db.session.commit()
        flash('User has been unblocked', category='success')
    else:
        flash('User does not exist', category='error')

    return redirect(url_for('views.admin'))

# ---------------------------------
# PUBLICACIONES (CREAR, VER, ELIMINAR)
# ---------------------------------

@views.route('/publications', methods=['GET', 'POST'])
@login_required
def publications():
    """
    Permite al usuario crear publicaciones con texto y archivos adjuntos opcionales.
    Además, lista sus publicaciones en formato paginado.
    """

    if request.method == 'POST':
        publication_raw = request.form.get('publication')
        publication = bleach.clean(publication_raw)  # Sanitizar el contenido para evitar XSS

        file = request.files.get('publication_file')
        filename = None

        # Procesar archivo adjunto
        if file and allowed_file_generic(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join('website', 'static', 'uploads', 'publications')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
        elif file and not allowed_file_generic(file.filename):
            flash('Unsupported file type.', category='error')
            return redirect(url_for('views.publications'))

        # Validar contenido
        if len(publication) > 0 or filename:
            new_publication = Publication(
                content=publication,
                user_id=current_user.id,
                file_path=filename
            )
            db.session.add(new_publication)
            db.session.commit()
            flash('Publication added', category='success')
            return redirect(url_for('views.publications'))
        else:
            flash('The content must contain at least one character or an attached file', category='error')

    # Mostrar publicaciones paginadas
    page = request.args.get('page', 1, type=int)
    per_page = 8
    user_publications = Publication.query.filter_by(user_id=current_user.id).order_by(Publication.date.desc()).paginate(page=page, per_page=per_page)

    return render_template("publications.html", user=current_user, user_publications=user_publications)

@views.route('/deletePublication', methods=['POST'])
@login_required
def deletePublication():
    """
    Permite al usuario eliminar sus propias publicaciones.
    """
    publication_id = request.form.get('publication_id')
    publication = Publication.query.get(publication_id)

    if publication:
        if publication.user_id == current_user.id:
            db.session.delete(publication)
            db.session.commit()
            flash('Publication deleted successfully', category='success')
            logging.info(f"User {current_user.email} deleted publication ID {publication_id}")
        else:
            flash('You are not authorized to delete this publication', category='error')
            logging.warning(f"Unauthorized delete attempt by {current_user.email} for publication ID {publication_id}")
    else:
        flash('Publication not found', category='error')
        logging.warning(f"User {current_user.email} attempted to delete non-existent publication ID {publication_id}")

    return redirect(url_for('views.publications'))

# ---------------------------------
# VER PERFIL Y PUBLICACIONES DE OTRO USUARIO
# ---------------------------------

@views.route('/viewuser/<email>')
@login_required
def viewuser(email):
    """
    Muestra las publicaciones de otro usuario.
    """
    user = User.query.filter_by(email=email).first()
    if user:
        page = request.args.get('page', 1, type=int)
        per_page = 8
        user_publications = Publication.query.filter_by(user_id=user.id)\
            .order_by(Publication.date.desc())\
            .paginate(page=page, per_page=per_page)

        return render_template("publications.html", user=user, user_publications=user_publications)
    else:
        flash('User not found', category='error')
        return render_template("userlist.html", user=current_user)

# ---------------------------------
# LISTA DE USUARIOS
# ---------------------------------

@views.route('/userlist')
@login_required
def userlist():
    """
    Muestra la lista de todos los usuarios excepto el actual.
    """
    users = User.query.filter(User.id != current_user.id).all()
    return render_template("userlist.html", users=users, user=current_user)

# ---------------------------------
# MENSAJES PRIVADOS ENTRE USUARIOS
# ---------------------------------

@views.route('/messages', methods=['GET'])
@login_required
def messages():
    """
    Muestra las conversaciones y permite seleccionar un usuario para ver los mensajes.
    """

    # Usuarios con los que se ha comunicado
    users_contacted = User.query.filter(
        User.id != current_user.id,
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == User.id),
            and_(Message.receiver_id == current_user.id, Message.sender_id == User.id)
        )
    ).distinct().all()

    selected_user_id = request.args.get('user_id', type=int)
    conversation = None

    if selected_user_id:
        conversation = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == selected_user_id),
                and_(Message.receiver_id == current_user.id, Message.sender_id == selected_user_id)
            )
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
    """
    Envía un mensaje privado a otro usuario. Permite adjuntar un archivo opcional.
    """
    receiver_email = request.form.get('receiver_email')
    content_raw = request.form.get('content')
    content = bleach.clean(content_raw)

    file = request.files.get('message_file')
    filename = None

    if not receiver_email or not content:
        flash('Receiver email and content are required', category='error')
        return redirect(url_for('views.messages'))

    receiver = User.query.filter_by(email=receiver_email).first()
    if not receiver:
        flash('User with this email does not exist!', category='error')
        return redirect(url_for('views.messages'))

    # Procesar archivo adjunto
    if file and allowed_file_generic(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join('website', 'static', 'uploads', 'messages')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
    elif file and not allowed_file_generic(file.filename):
        flash('Unsupported file type.', category='error')
        return redirect(url_for('views.messages'))

    # Crear y guardar el mensaje
    new_message = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=content,
        file_path=filename
    )
    db.session.add(new_message)
    db.session.commit()

    logging.info(f"User {current_user.email} sent a message to {receiver.email}")
    flash('Message sent', category='success')
    return redirect(url_for('views.messages'))
