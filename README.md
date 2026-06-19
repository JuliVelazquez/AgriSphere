# Configuración de Variables de Entorno (Desarrollo Local)

Para correr este proyecto en local sin usar Docker, debes configurar las siguientes variables de entorno en la raíz del proyecto.

1. Crea un archivo llamado `.env` copiando la estructura de `.env.example`.
2. Llena las siguientes variables con tus datos locales:

# Variables Requeridas:
* **DATABASE**: Ruta de conexión a tu base de datos PostgreSQL local usando la librería `asyncpg`. (Ejemplo: `postgresql+asyncpg://usuario:contraseña@localhost:5432/nombre_bd`).
* **SECRET_KEY**: Llave secreta utilizada para la firma y seguridad de los tokens de acceso (JWT). Cambiar por una cadena segura en local.
* **ALGORITHM**: Algoritmo de encriptación para los tokens (Valor por defecto: `HS256`).
* **ACCESS_TOKEN_EXPIRE_MINUTES**: Tiempo de vida de los tokens de sesión expresado en minutos (Valor sugerido: `480`).

