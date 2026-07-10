from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.database import get_db
from app.auth.utils import PermitirRoles
from app.auth.models import Usuario
from app.modulos.empresa.models import Invernadero, MonitoreoPlagas, PlantaRetirada
from app.modulos.dashboard.schemas import DashboardResumen, InvernaderoResumen, PlantaRetiradaResumen

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/resumen", response_model=DashboardResumen)
async def obtener_resumen_dashboard(
    current_user: dict = Depends(PermitirRoles(["Usuario", "Jefe Área", "Oficina"])),
    db: AsyncSession = Depends(get_db)
):
    usuario_id = int(current_user["sub"])
    
    resultado = await db.execute(
        select(Usuario).where(Usuario.id_usuario == usuario_id)
    )
    usuario = resultado.scalar_one_or_none()

    resultado_monitoreo = await db.execute(
        select(MonitoreoPlagas).order_by(MonitoreoPlagas.fecha.desc()).limit(1)
    )
    monitoreo = resultado_monitoreo.scalar_one_or_none()

    resultado_inv = await db.execute(select(Invernadero))
    invernaderos = resultado_inv.scalars().all()

    resultado_plantas = await db.execute(
        select(PlantaRetirada).order_by(PlantaRetirada.fecha.desc()).limit(10)
    )
    plantas = resultado_plantas.scalars().all()

    return DashboardResumen(
        usuario=usuario.nombre if usuario else "Desconocido",
        fecha_hora_servidor=datetime.now(),
        plagas_detectadas=monitoreo.plagas_detectadas if monitoreo else 0,
        insectos_beneficos=monitoreo.insectos_beneficos if monitoreo else 0,
        focos_enfermedad=monitoreo.focos_enfermedad if monitoreo else 0,
        nivel_alerta=monitoreo.nivel_alerta if monitoreo else "NORMAL",
        invernaderos=[
            InvernaderoResumen(
                nombre=inv.nombre,
                cultivo=inv.cultivo,
                estado=inv.estado,
                ultima_revision=inv.ultima_revision,
                responsable=inv.responsable
            ) for inv in invernaderos
        ],
        plantas_retiradas=[
            PlantaRetiradaResumen(
                tipo_problema=p.tipo_problema,
                cantidad=p.cantidad
            ) for p in plantas
        ]
    )