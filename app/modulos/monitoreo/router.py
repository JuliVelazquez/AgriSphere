from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date


from app.database import get_db

from app.modulos.monitoreo.models import (
    ReporteMonitoreo,
    ReporteObservable,
    CatalogoObservable,
    EvidenciaMonitoreo,
    ZonaInvernadero
)

from app.modulos.monitoreo.schemas import (
    HistorialResponse,
    ReporteMonitoreoCreate,
    CatalogoObservableResponse,
    ZonaInvernaderoResponse,
    DetalleMonitoreoResponse
)
from app.auth.utils import PermitirRoles

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

ROLES_MONITOREO = [
    "Usuario", 
    "Jefe Área",
    "Oficina"
]

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/reportes/historial", response_model=HistorialResponse) 
async def obtener_historial_monitoreo(
    fecha: Optional[date] = None,
    id_invernadero: Optional[int] = None,
    id_usuario: Optional[int] = None,
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el historial de reportes de monitoreo.
    Permite filtrar opcionalmente por fecha, invernadero o usuario.
    """
    # 1. Consulta base 
    query = select(ReporteMonitoreo).order_by(
    ReporteMonitoreo.fecha_registro.desc(),
    ReporteMonitoreo.id_reporte.desc()
    )

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

@router.get(
    "/reportes/{id_reporte}",
    response_model=DetalleMonitoreoResponse
)
async def obtener_detalle_monitoreo(
    id_reporte: int,
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
    resultado = await db.execute(
        select(ReporteMonitoreo)
        .options(
            selectinload(ReporteMonitoreo.observables),
            selectinload(ReporteMonitoreo.evidencias)
        )
        .where(
            ReporteMonitoreo.id_reporte == id_reporte
        )
    )

    reporte = resultado.scalar_one_or_none()

    if reporte is None:
        raise HTTPException(
            status_code=404,
            detail="Reporte de monitoreo no encontrado"
        )

    return {
        "status": "success",
        "data": reporte
    }

@router.post("/reportes")
async def crear_reporte_monitoreo(
    payload: ReporteMonitoreoCreate,
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Crear el reporte principal
        nuevo_reporte = ReporteMonitoreo(
            id_invernadero=payload.id_invernadero,
            id_usuario=int(
                current_user["sub"]
            ),
            zona=payload.zona,
            seccion=payload.seccion,
            temperatura=payload.temperatura,
            humedad=payload.humedad,
            tipo_observacion=payload.tipo_observacion,
            especie_tipo=payload.especie_tipo,
            nivel_infestacion=payload.nivel_infestacion,
            notas=payload.notas
        )

        db.add(nuevo_reporte)

        # 2. Hacer flush para obtener el id_reporte
        # SIN cerrar todavía la transacción
        await db.flush()

        # 3. Guardar todos los observables vinculados al reporte
        for observable in payload.observables:
            nuevo_observable = ReporteObservable(
                id_reporte=nuevo_reporte.id_reporte,
                punto_visible=observable.punto_visible,
                cantidad=observable.cantidad
            )

            db.add(nuevo_observable)

        # 4. Guardar reporte + observables juntos
        await db.commit()

        # 5. Refrescar para tener los datos finales
        await db.refresh(nuevo_reporte)

        # 6. Respuesta compatible con Android
        return {
            "id_reporte": nuevo_reporte.id_reporte,
            "fecha_registro": nuevo_reporte.fecha_registro,
            "id_invernadero": nuevo_reporte.id_invernadero,
            "id_usuario": nuevo_reporte.id_usuario
        }

    except Exception as error:
        await db.rollback()

        print("--- ERROR REAL EN EL ENDPOINT ---")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
    
# ===========================
# ENDPOINT PARA SUBIR FOTOS
# ===========================
# 1. Definimos la carpeta donde se guardarán las fotos
CARPETA_FOTOS = "static/fotos_monitoreo"
os.makedirs(CARPETA_FOTOS, exist_ok=True)

@router.post("/subir-fotos")
async def subir_fotos_evidencia(
    id_reporte: int = Form(...),
    fotos: List[UploadFile] = File(...),
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe fotografías, las guarda físicamente
    y las relaciona con un reporte de monitoreo.
    """

    # 1. Confirmar que el reporte realmente exista
    reporte = await db.get(ReporteMonitoreo, id_reporte)

    if reporte is None:
        raise HTTPException(
            status_code=404,
            detail="El reporte indicado no existe"
        )

    urls_definitivas = []
    archivos_guardados = []

    try:
        # 2. Guardar todas las fotografías
        for foto in fotos:

            # Obtener extensión original
            extension = os.path.splitext(foto.filename or "")[1]

            if not extension:
                extension = ".jpg"

            # Crear nombre único
            nombre_unico = f"{uuid.uuid4()}{extension}"

            # Ruta física
            ruta_archivo = os.path.join(
                CARPETA_FOTOS,
                nombre_unico
            )

            # Guardar archivo
            with open(ruta_archivo, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)

            archivos_guardados.append(ruta_archivo)

            # URL que podrá utilizar Android
            url_final = f"/{ruta_archivo}".replace("\\", "/")
            urls_definitivas.append(url_final)

            # 3. Relacionar foto con el reporte
            nueva_evidencia = EvidenciaMonitoreo(
                id_reporte=id_reporte,
                url_foto=url_final
            )

            db.add(nueva_evidencia)

        # 4. Guardar las relaciones en PostgreSQL
        await db.commit()

        return {
            "status": "success",
            "message": f"Se subieron  {len(fotos)} fotos correctamente",
            "urls": urls_definitivas
        }

    except Exception as error:

        await db.rollback()

        # Si algo falla, borrar también los archivos
        # que alcanzaron a guardarse.
        for ruta in archivos_guardados:
            if os.path.exists(ruta):
                os.remove(ruta)

        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@router.get("/catalogos/observables", response_model=List[CatalogoObservableResponse])
async def obtener_catalogo(
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
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

@router.get(
    "/invernaderos/{id_invernadero}/zonas",
    response_model=List[ZonaInvernaderoResponse]
)
async def obtener_zonas_invernadero(
    id_invernadero: int,
    current_user: dict = Depends(
        PermitirRoles(ROLES_MONITOREO)
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve las zonas activas pertenecientes
    al invernadero seleccionado.
    """

    resultado = await db.execute(
        select(ZonaInvernadero)
        .where(
            ZonaInvernadero.id_invernadero == id_invernadero,
            ZonaInvernadero.estado == "Activo"
        )
        .order_by(ZonaInvernadero.id_zona)
    )

    return resultado.scalars().all()

