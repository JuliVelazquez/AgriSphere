from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.modulos.empresa.models import Empresa
from app.modulos.empresa.schemas import EmpresaParametrosUpdate
from app.auth.utils import PermitirRoles
from .models import MarcajeReloj
from .schemas import MarcajeOutput, MarcajeInput
from app.auth.models import Usuario

router = APIRouter(prefix="/api/empresa", tags=["Configuración de Empresa"])

ROLES_ADMIN = ["Administrador", "Oficina", "Jefe Área"]

@router.put("/parametros/{empresa_id}")
async def actualizar_parametros_empresa(
    empresa_id: int,
    datos: EmpresaParametrosUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(PermitirRoles(ROLES_ADMIN))
):
    query = select(Empresa).where(Empresa.id == empresa_id)
    resultado = await db.execute(query)
    empresa = resultado.scalar_one_or_none()

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    datos_actualizar = datos.model_dump(exclude_unset=True)
    for clave, valor in datos_actualizar.items():
        setattr(empresa, clave, valor)

    await db.commit()
    await db.refresh(empresa)

    return {
        "mensaje": "Parámetros de empresa actualizados",
        "datos": empresa
    }

@router.get(
    "/api/reloj/marcajes",
    response_model=list[MarcajeOutput]
)
async def obtener_registro_marcajes(
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    resultado = await db.execute(
        select(MarcajeReloj, Usuario.nombre)
        .outerjoin(
            Usuario,
            Usuario.id_usuario == MarcajeReloj.empleado_id
        )
        .order_by(MarcajeReloj.id.desc())
    )

    registros = resultado.all()

    return [
        MarcajeOutput(
            id=marcaje.id,
            fecha=marcaje.fecha,
            hora=marcaje.hora,
            empleado_id=marcaje.empleado_id,
            nombre_empleado=nombre_usuario or "Desconocido",
            tipo_evento=marcaje.tipo_evento
        )
        for marcaje, nombre_usuario in registros
    ]


@router.post(
    "/api/reloj/marcajes",
    response_model=MarcajeOutput
)
async def crear_marcaje(
    datos: MarcajeInput,
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    # Comprobar primero que el empleado exista
    resultado_usuario = await db.execute(
        select(Usuario).where(
            Usuario.id_usuario == datos.empleado_id
        )
    )
    usuario = resultado_usuario.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Empleado no encontrado."
        )

    nuevo = MarcajeReloj(
        empleado_id=datos.empleado_id,
        tipo_evento=datos.tipo_evento
    )

    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)

    return MarcajeOutput(
        id=nuevo.id,
        fecha=nuevo.fecha,
        hora=nuevo.hora,
        empleado_id=nuevo.empleado_id,
        nombre_empleado=usuario.nombre,
        tipo_evento=nuevo.tipo_evento
    )