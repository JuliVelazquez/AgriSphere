from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from app.database import get_db  
from app.modulos.monitoreo.models import ReporteMonitoreo, ReporteObservable
from app.modulos.monitoreo.schemas import HistorialResponse, ReporteMonitoreoCreate
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
@router.post("/reportes")
async def crear_reporte_monitoreo(
    payload: ReporteMonitoreoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Motor de inserción del formulario. 
    Recibe un payload complejo y valida la estructura con Pydantic.
    """
    # 1. Crear el registro principal
    nuevo_reporte = ReporteMonitoreo(
        id_invernadero=payload.id_invernadero,
        id_usuario=payload.id_usuario,
        zona=payload.zona,
        seccion=payload.seccion,
        tipo_observacion=payload.tipo_observacion,
        especie_tipo=payload.especie_tipo,
        nivel_urgencia=payload.nivel_urgencia,
        notas=payload.notas,
        fecha_registro=date.today() 
    )
    db.add(nuevo_reporte)
    await db.flush() 
    
    # 2. Guardar el arreglo dinámico
    for obs in payload.observables:
        nuevo_observable = ReporteObservable( 
            id_reporte=nuevo_reporte.id_reporte,
            punto_visible=obs.punto_visible,
            cantidad=obs.cantidad
        )
        db.add(nuevo_observable)
    
    # 3. Confirmar la transacción
    await db.commit()

    return {
        "status": "success",
        "message": "Reporte principal y observables guardados correctamente",
        "id_generado": nuevo_reporte.id_reporte, # Le mandamos al front el ID nuevo como extra
        "datos_recibidos": payload.model_dump()
    }