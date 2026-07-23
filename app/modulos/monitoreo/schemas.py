from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional

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

# 3. Molde para cada elemento de arreglo de observables
class ObservableItem(BaseModel): 
    punto_visible: str = Field(..., description="Punto visible u observación") 
    cantidad: int = Field(..., gt=0, description="La cantidad debe ser mayor a cero")

# 4. Molde principal (payload complejo)
class ReporteMonitoreoCreate(BaseModel):
    id_invernadero: int  
    id_usuario: int
    zona: str
    seccion: str
    tipo_observacion: str
    especie_tipo: str
    nivel_urgencia: str
    notas: Optional[str]= None
    observables: List[ObservableItem]