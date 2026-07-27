from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.database import get_db
from app.auth.models import Usuario, ExpedienteTrabajador
from app.modulos.escaner.schemas import EscanerRequest, EscanerResponse
from app.modulos.empresa.models import Invernadero
from app.modulos.escaner.schemas import EscanerRequest, EscanerResponse, ZonaAsignada, AsignacionesResponse

router = APIRouter(prefix="/api/escaner", tags=["Escáner QR"])

@router.post("/validar", response_model=EscanerResponse)
async def validar_qr(
    payload: EscanerRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Parsear el string del QR: "usr_1:timestamp_1234567890:sig_ab89f3"
        partes = payload.qr_string.split(":")
        if len(partes) != 3:
            raise ValueError("Formato inválido")

        usuario_id = int(partes[0].replace("usr_", ""))
        timestamp_qr = int(partes[1].replace("timestamp_", ""))

        # 2. Validar que no haya expirado (60 segundos de vigencia)
        timestamp_actual = int(datetime.now(timezone.utc).timestamp())
        if timestamp_actual - timestamp_qr > 60:
            return EscanerResponse(
                status="denegado",
                acceso=False,
                mensaje="Código QR expirado. Pide al trabajador que genere uno nuevo."
            )

        # 3. Buscar al usuario en la base de datos
        resultado = await db.execute(
            select(Usuario).where(Usuario.id_usuario == usuario_id)
        )
        usuario = resultado.scalar_one_or_none()

        if not usuario:
            return EscanerResponse(
                status="denegado",
                acceso=False,
                mensaje="Usuario no encontrado."
            )

        # 4. Buscar su expediente para obtener el área/puesto
        resultado_exp = await db.execute(
            select(ExpedienteTrabajador).where(
                ExpedienteTrabajador.usuario_id == usuario_id
            )
        )
        expediente = resultado_exp.scalar_one_or_none()

        return EscanerResponse(
            status="concedido",
            acceso=True,
            mensaje="Acceso concedido.",
            nombre=usuario.nombre,
            puesto=expediente.area_rol if expediente else "Sin área asignada"
        )

    except Exception:
        return EscanerResponse(
            status="error",
            acceso=False,
            mensaje="QR inválido o mal formado."
        )

@router.get("/api/usuarios/{usuario_id}/asignaciones", response_model=AsignacionesResponse)
async def obtener_asignaciones(
    usuario_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 1. Buscar expediente del usuario
    resultado_exp = await db.execute(
        select(ExpedienteTrabajador).where(
            ExpedienteTrabajador.usuario_id == usuario_id
        )
    )
    expediente = resultado_exp.scalar_one_or_none()

    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado.")

    # 2. Buscar nombre del usuario
    resultado_usr = await db.execute(
        select(Usuario).where(Usuario.id_usuario == usuario_id)
    )
    usuario = resultado_usr.scalar_one_or_none()

    # 3. Leer access_level y buscar invernaderos que coincidan
    access_level = expediente.access_level or []
    
    resultado_inv = await db.execute(
        select(Invernadero).where(Invernadero.nombre.in_(access_level))
    )
    invernaderos = resultado_inv.scalars().all()

    return AsignacionesResponse(
        usuario_id=usuario_id,
        nombre=usuario.nombre if usuario else "Desconocido",
        asignaciones=[
            ZonaAsignada(
                invernadero_id=inv.id,
                nombre=inv.nombre,
                cultivo=inv.cultivo,
                estado=inv.estado
            ) for inv in invernaderos
        ]
    )