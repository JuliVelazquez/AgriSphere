from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List

# ==========================================
# 1. ESQUEMAS PARA AUTENTICACIÓN (LOGIN)
# ==========================================

# Esquema para capturar la latitud y longitud enviadas por la app móvil
class GeolocalizacionSchema(BaseModel):
    latitud: float = Field(..., examples=[21.5041])
    longitud: float = Field(..., examples=[-104.8945])

# Esquema exacto para la petición de Login (Request)
class LoginRequest(BaseModel):
    usuario: str = Field(..., examples=["julissa_rieg"])
    password: str = Field(..., examples=["lalala"])
    ui_device: str = Field(default="web_browser", examples=["v_chrome_windows"])

    # coordenadas opcionales para la validación de geo-cerca
    ubicacion: Optional[GeolocalizacionSchema] = None

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

    # ==========================================
# 5. ESQUEMAS PARA TRABAJADORES (RECURSOS HUMANOS)
# ==========================================

# Esquema para la información del Expediente (Tabla expedientes_trabajadores)
class ExpedienteBase(BaseModel):
    tipo_usuario: Optional[str] = Field(default="trabajador", examples=["trabajador"])
    estatus: Optional[str] = Field(default="base", examples=["base", "provicional", "baja"])
    empresa_id: Optional[int] = Field(default=1, examples=[1])
    empresa: Optional[str] = Field(default="Invernaderos Marquesado de Guadalupe", examples=["Invernaderos Marquesado de Guadalupe"])
    area_rol: Optional[str] = Field(None, examples=["sanidad"])
    actividad: Optional[str] = Field(None, examples=["monitoreo"])
    access_level: Optional[List[str]] = Field(default=[], examples=[["semillero", "invernadero_b"]])
    
    curp: Optional[str] = Field(None, max_length=18, examples=["ABC123456M100"])
    telefono: Optional[str] = Field(None, examples=["3312345678"])
    email: Optional[EmailStr] = Field(None, examples=["maria.lopez@ejemplo.com"])
    contacto: Optional[str] = Field(None, examples=["pajaritos 342 col alamos"])
    cp: Optional[str] = Field(None, examples=["98765"])
    
    salud: Optional[str] = Field(None, examples=["alergias / restricciones"])
    acepta: Optional[bool] = Field(default=True)
    historial: Optional[str] = Field(None, examples=["observaciones de encargados"])

# Esquema principal para el POST /api/trabajador
class TrabajadorCreate(BaseModel):
    # Datos que irán a la tabla 'usuarios'
    nombre_usuario: str = Field(..., examples=["maria_lopez"])
    contraseña: str = Field(..., examples=["secreto123"])
    nombre_completo: str = Field(..., examples=["María López Pérez"])
    rol_asignado: str = Field(default="Usuario", examples=["Usuario"])
    
    # Datos que irán a la tabla 'expedientes_trabajadores'
    expediente: ExpedienteBase

# ==========================================
# 6. ESQUEMAS PARA CONFIGURACIÓN DE EMPRESA
# ==========================================
class EmpresaConfig(BaseModel):
    nombre: str = Field(..., examples=["Invernadero Marquesado"])
    geocerca_latitud: float = Field(..., examples=[21.5041])
    geocerca_longitud: float = Field(..., examples=[-104.8945])
    geocerca_radio_metros: int = Field(default=50, description="Radio de la geocerca en metros", examples=[50])

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Invernadero Marquesado",
                "geocerca_latitud": 21.5041,
                "geocerca_longitud": -104.8945,
                "geocerca_radio_metros": 50
            }
        }
    }