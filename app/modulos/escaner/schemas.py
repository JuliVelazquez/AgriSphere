from pydantic import BaseModel

class EscanerRequest(BaseModel):
    qr_string: str

class EscanerResponse(BaseModel):
    status: str
    acceso: bool
    mensaje: str
    nombre: str = None
    puesto: str = None

class ZonaAsignada(BaseModel):
    invernadero_id: int
    nombre: str
    cultivo: str = None
    estado: str

class AsignacionesResponse(BaseModel):
    status: str = "success"
    usuario_id: int
    nombre: str
    asignaciones: list[ZonaAsignada]