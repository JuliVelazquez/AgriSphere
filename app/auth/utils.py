import os
import bcrypt
import math
from typing import List
from datetime import datetime, timedelta, timezone

from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

# ==========================================
# 1. CONFIGURACIÓN DE CONTRASEÑAS (BCRYPT NATIVO)
# ==========================================
def verificar_password(password_plano: str, password_encriptado: str) -> bool:
    """Compara la contraseña ingresada con la guardada en la BD usando bcrypt nativo."""
    password_bytes = password_plano.encode('utf-8')
    hash_bytes = password_encriptado.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def encriptar_password(password: str) -> str:
    """Genera un hash seguro usando bcrypt nativo."""
    password_bytes = password.encode('utf-8')
    sal = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(password_bytes, sal)
    return hash_bytes.decode('utf-8')


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
       
        try:
            # 1. Abrimos el token usando la configuración maestra de tu app
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            rol_usuario = payload.get("rol")
            
            # 2. Verificamos si su rol está en la lista permitida
            if rol_usuario not in self.roles_permitidos:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Acceso denegado. Tu rol es '{rol_usuario}', pero se requiere uno de estos: {self.roles_permitidos}"
                )
            
            # Si todo está bien, dejamos pasar la petición
            return payload
            
        except HTTPException:
            # Si es el error 403 de roles, lo dejamos salir tal cual
            raise
        except Exception as e:
            # Si es un error del token, lo imprimimos en la terminal para verlo
            print(f"FALLO DE TOKEN: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado. Por favor, inicia sesión nuevamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        

def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia en metros entre dos coordenadas GPS usando la fórmula de Haversine.
        """
        R = 6371000  # Radio de la Tierra en metros
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0) ** 2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c