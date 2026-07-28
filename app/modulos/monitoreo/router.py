from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select
from typing import Optional, List
from datetime import date
from app.database import get_db 
from app.modulos.monitoreo.models import ReporteMonitoreo, ReporteObservable, CatalogoObservable
from app.modulos.monitoreo.schemas import HistorialResponse, ReporteMonitoreoCreate, CatalogoObservableResponse
import os
import uuid
import shutil

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
        nivel_infestacion=payload.nivel_infestacion,
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

# ===========================
# ENDPOINT PARA SUBIR FOTOS
# ===========================
# 1. Definimos la carpeta donde se guardarán las fotos
CARPETA_FOTOS = "static/fotos_monitoreo"
os.makedirs(CARPETA_FOTOS, exist_ok=True)

@router.post("/subir-fotos")
async def subir_fotos_evidencia(fotos: List[UploadFile] = File(...)):
    """
    Recibe archivos fisicos, los guarda en el servidor
    y devuelve un arreglo con las URLs definitivas.
    """
    urls_definitivas = []
    for foto in fotos:
        # 1. Extraer la extensión del archivo (ej. .jpg, .png)
        extension = foto.filename.split(".")[-1]

        # 2. Crear un nombre único para que no choquen los archivos
        nombre_unico = f"{uuid.uuid4()}.{extension}"

        # 3. Armar la ruta completa donde se guardará
        ruta_archivo = os.path.join(CARPETA_FOTOS, nombre_unico)

        # 4. Guardar el archivo fisico en el servidor
        with open(ruta_archivo, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

        # 5. Generar la "URL" que le regresaremos a Android
        url_final = f"/{ruta_archivo}".replace("\\", "/")
        urls_definitivas.append(url_final)

# 6. Devolver el arreglo con las URLs como pide el requerimiento
    return{
      "status": "success",
      "message": f"Se subieron{len(fotos)} fotos correctamente",
      "urls": urls_definitivas
}

@router.get("/catalogos/observables", response_model=List[CatalogoObservableResponse])
async def obtener_catalogo(db: AsyncSession = Depends(get_db)):
    """
    Extrae el catálogo completo de observables para popular los 
    menús en cascada (Plagas, Enfermedades, Insectos Benéficos).
    """
    # Hacemos la consulta a la nueva tabla
    query = select(CatalogoObservable)
    result = await db.execute(query)
    
    # Extraemos todos los registros
    catalogos = result.scalars().all()
    
    return catalogos