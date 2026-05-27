from pydantic import BaseModel, Field

# Esquema para capturar la latitud y longitud enviadas por la app móvil
class GeolocalizacionSchema(BaseModel):
    latitud: float = Field(..., examples=[21.5041])
    longitud: float = Field(..., examples=[-104.8945])

# Esquema exacto para la petición de Login (Request)
class LoginRequest(BaseModel):
    usuario: str = Field(..., examples=["empleado_01"])
    password: str = Field(..., examples=["password_seguro_2026"])
    ui_device: str = Field(..., examples=["Device-Model-Plus"])
    geolocalizacion: GeolocalizacionSchema

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