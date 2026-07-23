from pydantic import BaseModel
from datetime import date
from typing import List

# 1. Molde de un solo reporte
class ReporteMonitoreoResponse(BaseModel):
    id_reporte: int
    fecha_registro: date
    id_invernadero: int
    id_usuario: int

    class Config:
        from_attributes = True  # importante para que Pydantic entienda a SQLAlchemy

# 2. Molde de la respuesta completa
class HistorialResponse(BaseModel):
    status: str 
    message: str
    data: List[ReporteMonitoreoResponse]
