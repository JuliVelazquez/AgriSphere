from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from app.database import get_db  
from app.modulos.monitoreo.models import ReporteMonitoreo
from app.modulos.monitoreo.schemas import HistorialResponse
# ==========================================
# CONFIGURACIÓN DEL ROUTER
# ==========================================
router = APIRouter(
    prefix="/api/monitoreo",
    tags=["Historial y Reportes de Monitoreo"]
)

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/reportes/historial", response_model=HistorialResponse) 
async def obtener_historial_monitoreo(
    fecha: Optional[date] = None,
    id_invernadero: Optional[int] = None,
    id_usuario: Optional[int] = None,
    db: AsyncSession = Depends(get_db)  # Es la llave de tu base de datos
):
    """
    Obtiene el historial de reportes de monitoreo.
    Permite filtrar opcionalmente por fecha, invernadero o usuario.
    """
    # 1. Consulta base 
    query = select(ReporteMonitoreo) 

    # 2. Filtros dinámicos 
    if fecha:
        query = query.where(ReporteMonitoreo.fecha_registro == fecha)
        
    if id_invernadero:
        query = query.where(ReporteMonitoreo.id_invernadero == id_invernadero)
        
    if id_usuario:
        query = query.where(ReporteMonitoreo.id_usuario == id_usuario)

    # 3. Ejecución real en la base de datos asíncrona
    result = await db.execute(query) 
    reportes_db = result.scalars().all() 

    # 4. Retorno de la información
    return {
        "status": "success",
        "message": "Historial obtenido correctamente",
        "data": reportes_db
    }