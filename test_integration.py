import pytest
from website import create_app, db
from website.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def user(app):
    user = User(
        name="Integration",
        surname="User",
        email="integration@example.com",
        password=generate_password_hash("integrationpass")
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def client(app):
    return app.test_client()

def register_user(client, name, surname, email, password):
    # Función auxiliar para registrar usuarios y hacer logout para evitar sesiones abiertas
    client.post("/signup", data={
        "name": name,
        "surname": surname,
        "email": email,
        "password": password,
        "password2": password
    }, follow_redirects=True)
    client.get("/logout", follow_redirects=True)

# --------- INTEGRACIÓN: Registro + Login + Publicación ---------

def test_register_login_create_publication(client):
    # Registrar nuevo usuario
    register_user(client, "Integration", "Tester", "integration@example.com", "password123")

    # Login con el nuevo usuario
    response = client.post("/login", data={
        "email": "integration@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert b"Logged in successfully" in response.data

    # Crear publicación
    response = client.post("/publications", data={
        "publication": "Mi primera publicación de integración"
    }, follow_redirects=True)
    assert b"Publication added" in response.data

# --------- INTEGRACIÓN: Admin bloquea y desbloquea usuario ---------

def test_admin_block_unblock_user_flow(client, app):
    # Crear admin y usuario normal mediante el formulario de registro
    register_user(client, "Admin", "User", "admin@example.com", "adminpass")
    register_user(client, "User", "Normal", "user@example.com", "userpass")

    # Convertir al usuario admin en administrador (role=0)
    with app.app_context():
        admin_user = User.query.filter_by(email="admin@example.com").first()
        admin_user.role = 0
        db.session.commit()

        user = User.query.filter_by(email="user@example.com").first()
        user_id = user.id  # Guardar ID para bloquear/desbloquear

    # Login como admin
    client.post("/login", data={"email": "admin@example.com", "password": "adminpass"}, follow_redirects=True)

    # Bloquear usuario
    response = client.post(f"/block_user/{user_id}", follow_redirects=True)
    assert b"User blocked" in response.data

    # Logout admin
    client.get("/logout", follow_redirects=True)

    # Intentar login con usuario bloqueado
    response = client.post("/login", data={"email": "user@example.com", "password": "userpass"}, follow_redirects=True)
    assert b"This account has been blocked" in response.data

    # Login como admin de nuevo
    client.post("/login", data={"email": "admin@example.com", "password": "adminpass"}, follow_redirects=True)

    # Desbloquear usuario
    response = client.post(f"/unblock_user/{user_id}", follow_redirects=True)
    assert b"User has been unblocked" in response.data

    # Logout admin
    client.get("/logout", follow_redirects=True)

    # Login con usuario desbloqueado
    response = client.post("/login", data={"email": "user@example.com", "password": "userpass"}, follow_redirects=True)
    assert b"Logged in successfully" in response.data

# --------- INTEGRACIÓN: Enviar y recibir mensajes ---------

############################################################

def test_change_password(client, user):
    client.post("/login", data={"email": user.email, "password": "password123"}, follow_redirects=True)
    
    response = client.post("/change_password", data={
        "old_password": "password123",
        "new_password": "newpassword456",
        "new_password2": "newpassword456"
    }, follow_redirects=True)

    assert b"Password updated successfully" in response.data

    # Logout
    client.get("/logout", follow_redirects=True)

    # Login con la nueva contraseña
    response = client.post("/login", data={"email": user.email, "password": "newpassword456"}, follow_redirects=True)
    assert b"Logged in successfully" in response.data

def test_update_profile(client, user):
    client.post("/login", data={"email": user.email, "password": "password123"}, follow_redirects=True)

    response = client.post("/update_profile", data={
        "name": "NewName",
        "surname": "NewSurname"
    }, follow_redirects=True)

    assert b"Profile updated" in response.data

def test_blocked_user_cannot_create_publication(client, app):
    with app.app_context():
        user = User(name="Blocked", surname="User", email="blocked@example.com", password=generate_password_hash("password123"), is_blocked=True)
        db.session.add(user)
        db.session.commit()

    client.post("/login", data={"email": "blocked@example.com", "password": "password123"}, follow_redirects=True)

    response = client.post("/publications", data={
        "publication": "No debería poder publicarse esto."
    }, follow_redirects=True)

    assert b"Your account is blocked" in response.data


