from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.modulos.empresa.models import Empresa
from app.modulos.empresa.schemas import EmpresaParametrosUpdate
from app.auth.utils import PermitirRoles

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