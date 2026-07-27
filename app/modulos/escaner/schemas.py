from pydantic import BaseModel

class EscanerRequest(BaseModel):
    qr_string: str

class EscanerResponse(BaseModel):
    status: str
    acceso: bool
    mensaje: str
    nombre: str = None
    puesto: str = None