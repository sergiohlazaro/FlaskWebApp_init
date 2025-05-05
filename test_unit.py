import pytest
from website import create_app, db
from website.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    # Crea y configura una instancia de la aplicación para pruebas
    app = create_app()
    app.config.update({
        "TESTING": True,  # Modo testing para evitar efectos secundarios
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Base de datos en memoria
        "WTF_CSRF_ENABLED": False  # Desactivar CSRF para simplificar las pruebas
    })

    with app.app_context():
        db.create_all()
        yield app

        # Limpiar la base de datos después de cada prueba
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    # Cliente de pruebas que simula peticiones HTTP
    return app.test_client()

def create_user(email="unit@example.com", password="password123"):
    # Función auxiliar para crear un usuario
    return User(
        name="Unit",
        surname="Tester",
        email=email,
        password=generate_password_hash(password)
    )

@pytest.fixture
def user(app):
    # Fixture para crear un usuario en la base de datos para usar en pruebas
    user = create_user()
    db.session.add(user)
    db.session.commit()
    return user

def test_signup_success(client):
    # Prueba para registrar un usuario con datos válidos
    response = client.post("/signup", data={
        "name": "Test", 
        "surname": "User", 
        "email": "testuser@example.com", 
        "password": "password123", 
        "password2": "password123"
    }, follow_redirects=True)
    assert b"Account created successfully" in response.data

def test_signup_duplicate(client, user):
    # Prueba para registrar un usuario con un email ya existente
    response = client.post("/signup", data={
        "name": "Test", 
        "surname": "User", 
        "email": "unit@example.com", 
        "password": "password123", 
        "password2": "password123"
    }, follow_redirects=True)
    assert b"Email already exists" in response.data

# --------- LOGIN ---------

def test_login_success(client, user):
    # Prueba de login con credenciales correctas
    response = client.post("/login", data={
        "email": user.email,
        "password": "password123"
    }, follow_redirects=True)
    assert b"Logged in successfully" in response.data

def test_login_wrong_password(client, user):
    # Prueba de login con contraseña incorrecta
    response = client.post("/login", data={
        "email": user.email,
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Incorrect password" in response.data

# --------- PUBLICACIONES ---------

def test_create_valid_publication(client, user):
    # Prueba para crear una publicación válida
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/publications", data={
        "publication": "Esto es un post válido"
    }, follow_redirects=True)
    assert b"Publication added" in response.data

def test_create_invalid_publication(client, user):
    # Prueba para intentar crear una publicación vacía (inválida)
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/publications", data={
        "publication": ""
    }, follow_redirects=True)
    assert b"The content must contain at least one character" in response.data

# --------- MENSAJES ---------

def test_send_message_nonexistent_user(client, user):
    # Prueba para enviar un mensaje a un usuario inexistente
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/send_message", data={
        "receiver_email": "notexist@example.com",
        "content": "Hola!"
    }, follow_redirects=True)
    assert b"User with this email does not exist!" in response.data

# --------- PERFIL ---------

def test_update_bio_valid(client, user):
    # Prueba para actualizar la bio con un texto válido
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/update_bio", data={
        "bio": "Esta es mi nueva bio"
    }, follow_redirects=True)
    assert b"Your bio has been updated" in response.data

def test_update_bio_too_long(client, user):
    # Prueba para actualizar la bio con un texto demasiado largo
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    long_bio = "A" * 101
    response = client.post("/update_bio", data={
        "bio": long_bio
    }, follow_redirects=True)
    assert b"Bio too long" in response.data

# --------- ACCESO SIN LOGIN ---------

def test_access_publications_without_login(client):
    # Prueba para intentar acceder a publicaciones sin iniciar sesión
    response = client.get("/publications", follow_redirects=True)
    assert b"Login" in response.data  # Comprobar que redirige a la página de login
