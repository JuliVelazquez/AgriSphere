from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

# ==========================================
# 1. ESQUEMAS PARA AUTENTICACIÓN (LOGIN)
# ==========================================

# Esquema para capturar la latitud y longitud enviadas por la app móvil
class GeolocalizacionSchema(BaseModel):
    latitud: float = Field(..., examples=[21.5041])
    longitud: float = Field(..., examples=[-104.8945])

# Esquema exacto para la petición de Login (Request)
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    usuario: str = Field(..., examples=["julissa_rieg"])
    password: str = Field(..., examples=["lalala"])
    ui_device: str = Field(default="web_browser", examples=["v_chrome_windows"])

    # informacion de usuario para la prueba
    model_config = {
        "json_schema_extra": {
            "example": {
                "usuario": "julissa_rieg",
                "password": "lalala",
                "ui_device": "web_browser"
            }
        }
    }
# Esquema para los datos que regresaremos dentro del Token (Data Payload)
class TokenDataResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    rol: str

# Esquema final de respuesta exitosa (200 OK)
class LoginResponse(BaseModel):
    status: str = "success"
    message: str = "Autenticación correcta"
    data: TokenDataResponse


# ==========================================
# 2. ESQUEMAS PARA CÓDIGOS QR
# ==========================================

class QRData(BaseModel):
    qr_string_data: str
    expires_in_seconds: int

class QRResponse(BaseModel):
    status: str = "success"
    data: QRData


# ==========================================
# 3. ESQUEMAS PARA OFICINA (ALTA DE USUARIOS)
# ==========================================

class DatosContacto(BaseModel):
    email: EmailStr = Field(..., examples=["juan@empresa.com"])
    telefono: str = Field(..., examples=["3223456789"])

class UsuarioCreateRequest(BaseModel):
    nombre_usuario: str = Field(..., examples=["figaro_ortiz"])
    password_plano: str = Field(..., examples=["Invernadero2026*"])
    rol_asignado: str = Field(..., examples=["rol_rieg"])  # Se envía el ID del RBAC agrícola
    datos_contacto: DatosContacto

class UsuarioCreateData(BaseModel):
    usuario_id: int
    usuario: str
    rol: str
    status_sistema: str
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

class UsuarioCreateResponse(BaseModel):
    status: str = "success"
    message: str = "Usuario creado y credenciales encriptadas correctamente"
    data: UsuarioCreateData


# ==========================================
# 4. ESQUEMAS PARA OFICINA (PASS-MATCH)
# ==========================================

class PassMatchRequest(BaseModel):
    usuario: str = Field(..., examples=["figaro_ortiz"])
    password_a_verificar: str = Field(..., examples=["Invernadero2026*"])