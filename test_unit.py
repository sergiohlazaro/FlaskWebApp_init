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

        # Limpiar base de datos después de cada test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_user(email="unit@example.com", password="password123"):
    return User(
        name="Unit",
        surname="Tester",
        email=email,
        password=generate_password_hash(password)
    )

@pytest.fixture
def user(app):
    user = create_user()
    db.session.add(user)
    db.session.commit()
    return user

# --------- SIGNUP ---------

def test_signup_success(client):
    response = client.post("/signup", data={
        "name": "Test", 
        "surname": "User", 
        "email": "testuser@example.com", 
        "password": "password123", 
        "password2": "password123"
    }, follow_redirects=True)
    assert b"Account created successfuly" in response.data

def test_signup_duplicate(client, user):
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
    response = client.post("/login", data={
        "email": user.email,
        "password": "password123"
    }, follow_redirects=True)
    assert b"Logged in successfully" in response.data

def test_login_wrong_password(client, user):
    response = client.post("/login", data={
        "email": user.email,
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Incorrect password" in response.data

# --------- PUBLICACIONES ---------

def test_create_valid_publication(client, user):
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/publications", data={
        "publication": "Esto es un post válido"
    }, follow_redirects=True)
    assert b"Publication added" in response.data

def test_create_invalid_publication(client, user):
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
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    response = client.post("/update_bio", data={
        "bio": "Esta es mi nueva bio"
    }, follow_redirects=True)
    assert b"Your bio has been updated" in response.data

def test_update_bio_too_long(client, user):
    client.post("/login", data={
        "email": user.email,
        "password": "password123"
    })
    long_bio = "A" * 101
    response = client.post("/update_bio", data={
        "bio": long_bio
    }, follow_redirects=True)
    assert b"Bio too long" in response.data