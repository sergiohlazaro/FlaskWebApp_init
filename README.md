# FlaskWebApp_init
Initial Flask web app
-------------------------------
## Default users for test:
admin.admin@admin.com

admin
-------------------------------
user1@user.com

password1
-------------------------------
## Pruebas Unitarias
## Descripción
- Este conjunto de pruebas unitarias está diseñado para verificar el correcto funcionamiento de las principales funcionalidades de la aplicación web desarrollada.
- Las pruebas son ejecutadas utilizando pytest y una base de datos SQLite en memoria, lo que garantiza que son rápidas y no afectan a los datos reales.

### ¿Qué cubren las pruebas?
- Las pruebas están organizadas en distintas categorías que reflejan las funcionalidades clave de la aplicación:

### Autenticación
- Registro exitoso de usuario.

- Prevención de registros duplicados por email.

- Inicio de sesión exitoso.

- Prevención de inicio de sesión con contraseñas incorrectas.

### Publicaciones
- Creación de publicaciones válidas.

- Prevención de publicaciones vacías.

### Mensajes
- Prevención de envío de mensajes a usuarios inexistentes.

### Perfil
- Actualización de bio con contenido válido.

- Prevención de actualización de bio demasiado larga.

### Seguridad / Acceso
- Acceso no autorizado a publicaciones redirige al login.

### Notas importantes
- La base de datos se crea en memoria para cada ejecución de las pruebas. Esto significa que siempre está limpia.

- No se crean usuarios iniciales automáticos gracias a la condición if not app.config.get("TESTING") en __init__.py.

- CSRF desactivado en pruebas para simplificar las peticiones POST.

- Login simulado para pruebas que requieren autenticación.

- Mensajes flash y respuestas HTML evaluados por contenido para validar resultados.

### Conclusión
- Estas pruebas garantizan que los componentes individuales de la aplicación funcionan correctamente y que los errores comunes están controlados.
- Además, permiten detectar errores de forma rápida durante el desarrollo y previenen regresiones cuando se realizan cambios en el código.

