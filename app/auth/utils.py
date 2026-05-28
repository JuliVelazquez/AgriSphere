import os
from typing import List
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

# ==========================================
# 1. CONFIGURACIÓN DE CONTRASEÑAS (BCRYPT)
# ==========================================
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"], 
    deprecated="auto"
)

def verificar_password(password_plano: str, password_encriptado: str) -> bool:
    """Compara la contraseña ingresada con la guardada en la BD."""
    return pwd_context.verify(password_plano, password_encriptado)

def encriptar_password(password: str) -> str:
    """Genera un hash seguro."""
    return pwd_context.hash(password)


# ==========================================
# 2. CREACIÓN DE TOKENS JWT
# ==========================================
def crear_token_acceso(data: dict) -> str:
    """Genera el token JWT con la estructura de AgriSphere."""
    ahora = datetime.now(timezone.utc)
    tiempo_expiracion = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload exacto basado en la especificación técnica
    payload = {
        "sub": data.get("sub"),
        "rol": data.get("rol"),
        "device_id": data.get("device_id"),
        "iat": int(ahora.timestamp()),     
        "exp": int(tiempo_expiracion.timestamp()) 
    }
    
    # Firmamos el token con la configuración del archivo .env
    token_encriptado = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token_encriptado


# ==========================================
# 3. SEGURIDAD Y PROTECCIÓN DE RUTAS (ROLES)
# ==========================================
# Esquema de seguridad para leer el token de los headers (Bearer Token)
oauth2_scheme = HTTPBearer()

class PermitirRoles:
    """
    Dependencia de FastAPI para proteger rutas. 
    Verifica que el usuario tenga un token válido y un rol autorizado.
    """
    def __init__(self, roles_permitidos: List[str]):
        self.roles_permitidos = roles_permitidos

    async def __call__(self, credenciales: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
        token = credenciales.credentials
        
        # Leemos las llaves maestras desde el entorno
        secret_key = os.getenv("SECRET_KEY", "super_secret_key_2026_cambiar_esto_en_produccion")
        algorithm = os.getenv("ALGORITHM", "HS256")
        
        try:
            # 1. Abrimos el token JWT usando 'jose'
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            rol_usuario = payload.get("rol")
            
            # 2. Verificamos si su rol está en la lista permitida
            if rol_usuario not in self.roles_permitidos:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Acceso denegado. Esta acción requiere uno de estos roles: {self.roles_permitidos}"
                )
            
            # Si todo está bien, dejamos pasar la petición
            return payload
            
        except Exception:
            # Si el token expiró o fue alterado
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado. Por favor, inicia sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )