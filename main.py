# Importa la función create_app desde el paquete "website".
# Esta función está definida en __init__.py y se encarga de crear y configurar toda la aplicación de Flask,
# incluyendo extensiones como SQLAlchemy, CSRF, LoginManager, Blueprints, etc.
from website import create_app

# Llama a create_app() → esto devuelve una instancia de Flask que está totalmente configurada
app = create_app()

# Este bloque se ejecuta solo si este archivo se ejecuta directamente (ejemplo: python main.py).
# Es muy útil porque permite que este archivo actúe como punto de entrada sin interferir si se importa desde otro archivo.
if __name__ == '__main__':
    # Inicia el servidor de desarrollo de Flask
    # debug=True → Esto permite reinicio automático al detectar cambios en el código + muestra errores detallados en navegador
    app.run(debug=False)
