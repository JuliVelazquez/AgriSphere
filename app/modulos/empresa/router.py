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

@router.get("/api/reloj/marcajes", response_model=list[MarcajeOutput])
async def obtener_registro_marcajes(db: AsyncSession = Depends(get_db)):
    resultado = await db.execute(
        select(MarcajeReloj)
    )
    registros = resultado.scalars().all()
    
    output = []
    for r in registros:
        output.append(MarcajeOutput(
            id=r.id,
            fecha=r.fecha,
            hora=r.hora,
            empleado_id=r.empleado_id,
            nombre_empleado= "Pendiente",
            tipo_evento=r.tipo_evento
        ))
        
    return output

@router.post("/api/reloj/marcajes", response_model=MarcajeOutput)
async def crear_marcaje(
    datos: MarcajeInput,
    db: AsyncSession = Depends(get_db)
):
    nuevo = MarcajeReloj(
        empleado_id=datos.empleado_id,
        tipo_evento=datos.tipo_evento
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)

    resultado = await db.execute(
        select(Usuario).where(Usuario.id_usuario == nuevo.empleado_id)
    )
    usuario = resultado.scalar_one_or_none()

    return MarcajeOutput(
        id=nuevo.id,
        fecha=nuevo.fecha,
        hora=nuevo.hora,
        empleado_id=nuevo.empleado_id,
        nombre_empleado=usuario.nombre if usuario else "Desconocido",
        tipo_evento=nuevo.tipo_evento
    )