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
# Casos de prueba: TC-001, TC-004, TC-019

def test_register_login_create_publication(client):
    # TC-001: Registrar nuevo usuario con datos válidos
    register_user(client, "Integration", "Tester", "integration@example.com", "password123")

    # TC-004: Login con el nuevo usuario
    response = client.post("/login", data={
        "email": "integration@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert b"Logged in successfully" in response.data

    # TC-019: Crear publicación con contenido válido
    response = client.post("/publications", data={
        "publication": "Mi primera publicación de integración"
    }, follow_redirects=True)
    assert b"Publication added" in response.data

# --------- INTEGRACIÓN: Admin bloquea y desbloquea usuario ---------
# Casos de prueba: TC-007, TC-028, TC-029

def test_admin_block_unblock_user_flow(client, app):
    # Crear admin y usuario normal
    register_user(client, "Admin", "User", "admin@example.com", "adminpass")
    register_user(client, "User", "Normal", "user@example.com", "userpass")

    # Convertir usuario admin a rol administrador
    with app.app_context():
        admin_user = User.query.filter_by(email="admin@example.com").first()
        admin_user.role = 0
        db.session.commit()

        user = User.query.filter_by(email="user@example.com").first()
        user_id = user.id  # ID necesario para bloquear/desbloquear

    # Login como admin
    client.post("/login", data={"email": "admin@example.com", "password": "adminpass"}, follow_redirects=True)

    # TC-028: Bloquear usuario desde panel admin
    response = client.post(f"/block_user/{user_id}", follow_redirects=True)
    assert b"User blocked" in response.data

    # Logout admin
    client.get("/logout", follow_redirects=True)

    # TC-007: Intento de login por parte de usuario bloqueado
    response = client.post("/login", data={"email": "user@example.com", "password": "userpass"}, follow_redirects=True)
    assert b"This account has been blocked" in response.data

    # Login como admin de nuevo
    client.post("/login", data={"email": "admin@example.com", "password": "adminpass"}, follow_redirects=True)

    # TC-029: Desbloquear usuario desde panel admin
    response = client.post(f"/unblock_user/{user_id}", follow_redirects=True)
    assert b"User has been unblocked" in response.data

    # Logout admin
    client.get("/logout", follow_redirects=True)

    # Verificación de login exitoso después del desbloqueo
    response = client.post("/login", data={"email": "user@example.com", "password": "userpass"}, follow_redirects=True)
    assert b"Logged in successfully" in response.data
