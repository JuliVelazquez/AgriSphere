from pydantic import BaseModel, Field
from typing import Optional

class EmpresaParametrosUpdate(BaseModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    tamano_hectareas: Optional[float] = None
    rfc: Optional[str] = None
    estado_republica: Optional[str] = None
    logotipo: Optional[str] = None
    cultivos: Optional[str] = None
    
    # Parámetros del Checador
    geocerca_latitud: Optional[float] = Field(None, description="Latitud central de la empresa")
    geocerca_longitud: Optional[float] = Field(None, description="Longitud central de la empresa")
    geocerca_radio_metros: Optional[int] = Field(None, description="Radio permitido para checar entrada")

    # Etiquetas dinámicas
    label_invernadero: Optional[str] = None
    label_boli: Optional[str] = None
    label_zona1: Optional[str] = None
    label_zona2: Optional[str] = None
    label_seccion: Optional[str] = None
    label_surco: Optional[str] = None
    
    encargado_almacen_id: Optional[int] = None

    class Config:
        from_attributes = True