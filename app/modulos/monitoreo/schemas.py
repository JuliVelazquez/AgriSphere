from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


# ==========================================
# HISTORIAL DE MONITOREO
# ==========================================

# 1. Molde de un solo reporte para la lista del historial
class ReporteMonitoreoResponse(BaseModel):
    id_reporte: int
    fecha_registro: date
    id_invernadero: int
    id_usuario: int
    nivel_infestacion: str

    class Config:
        from_attributes = True


# 2. Molde de la respuesta completa del historial
class HistorialResponse(BaseModel):
    status: str
    message: str
    data: List[ReporteMonitoreoResponse]


# ==========================================
# DETALLE DE UN REPORTE
# ==========================================

# Observable registrado dentro de un reporte
class ObservableDetalleResponse(BaseModel):
    id_observable: int
    punto_visible: str
    cantidad: int

    class Config:
        from_attributes = True


# Fotografía relacionada con un reporte
class EvidenciaDetalleResponse(BaseModel):
    id_evidencia: int
    url_foto: str

    class Config:
        from_attributes = True


# Información completa de un reporte
class ReporteMonitoreoDetalleData(BaseModel):
    id_reporte: int
    fecha_registro: date
    id_invernadero: int
    id_usuario: int

    zona: str
    seccion: str

    temperatura: Optional[float] = None
    humedad: Optional[float] = None

    tipo_observacion: str
    especie_tipo: str
    nivel_infestacion: str
    notas: Optional[str] = None

    observables: List[ObservableDetalleResponse]
    evidencias: List[EvidenciaDetalleResponse]

    class Config:
        from_attributes = True


# Respuesta del endpoint GET /reportes/{id_reporte}
class DetalleMonitoreoResponse(BaseModel):
    status: str
    data: ReporteMonitoreoDetalleData


# ==========================================
# CREACIÓN DE REPORTES
# ==========================================

# 3. Molde para cada elemento del arreglo de observables
class ObservableItem(BaseModel):
    punto_visible: str = Field(
        ...,
        description="Punto visible u observación"
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="La cantidad debe ser mayor a cero"
    )


# 4. Molde principal del reporte
class ReporteMonitoreoCreate(BaseModel):
    id_invernadero: int
    id_usuario: int
    zona: str
    seccion: str
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    tipo_observacion: str
    especie_tipo: str
    nivel_infestacion: str
    notas: Optional[str] = None
    observables: List[ObservableItem]


# ==========================================
# CATÁLOGOS
# ==========================================

# 5. Molde para el catálogo de observables
class CatalogoObservableResponse(BaseModel):
    id_observable: int
    tipo: str
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# ZONAS DE INVERNADERO
# ==========================================

class ZonaInvernaderoResponse(BaseModel):
    id_zona: int
    nombre: str
    estado: str

    class Config:
        from_attributes = True