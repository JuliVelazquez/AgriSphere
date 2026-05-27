from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

# Configuración del contenedor de encriptación usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(password_plano: str, password_encriptado: str) -> bool:
    """Compara la contraseña ingresada con la guardada en la BD."""
    return pwd_context.verify(password_plano, password_encriptado)

def encriptar_password(password: str) -> str:
    """Genera un hash seguro (útil para cuando la oficina cree usuarios nuevos)."""
    return pwd_context.hash(password)

def crear_token_acceso(usuario_id: int, rol: str, device_id: str) -> str:
    """Genera el token JWT con la estructura exacta definida en la documentación."""
    ahora = datetime.now(timezone.utc)
    tiempo_expiracion = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload exacto basado en la especificación técnica de AgriSphere
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "device_id": device_id,
        "iat": int(ahora.timestamp()),     # Timestamp en formato Unix
        "exp": int(tiempo_expiracion.timestamp()) # Timestamp de expiración Unix
    }
    
    # Firmamos el token con la configuración del archivo .env
    token_encriptado = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token_encriptado