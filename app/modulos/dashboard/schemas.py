from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InvernaderoResumen(BaseModel):
    nombre: str
    cultivo: Optional[str] = None
    estado: str
    ultima_revision: Optional[datetime] = None
    responsable: Optional[str] = None

class PlantaRetiradaResumen(BaseModel):
    tipo_problema: str
    cantidad: int

class DashboardResumen(BaseModel):
    status: str = "success"
    usuario: str
    fecha_hora_servidor: datetime
    plagas_detectadas: int
    insectos_beneficos: int
    focos_enfermedad: int
    nivel_alerta: str
    invernaderos: List[InvernaderoResumen]
    plantas_retiradas: List[PlantaRetiradaResumen]