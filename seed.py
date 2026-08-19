import asyncio

from sqlalchemy.future import select

from app.database import AsyncSessionLocal, engine
from app.auth.models import Base, Usuario, UserRole
from app.auth.utils import encriptar_password
from app.modulos.empresa.models import Empresa


async def poblar_base_datos():
    print("Conectando a PostgreSQL y verificando tablas...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tablas verificadas/creadas.")

    async with AsyncSessionLocal() as session:
        async with session.begin():

            # Usuario inicial
            usuario_test = "julissa_rieg"

            resultado_usr = await session.execute(
                select(Usuario).where(
                    Usuario.usuario == usuario_test
                )
            )

            usuario_existente = resultado_usr.scalar_one_or_none()

            if not usuario_existente:
                nuevo_usuario = Usuario(
                    nombre="Julissa Velazquez",
                    usuario=usuario_test,
                    contraseña=encriptar_password("lalala"),
                    rol=UserRole.USUARIO,
                    correo="julissa.velazquez@agrisphere.com",
                    telefono="3111234501"
                )

                session.add(nuevo_usuario)
                await session.flush()

                id_julissa = nuevo_usuario.id_usuario

                print(
                    f"Usuario inicial creado: {usuario_test}"
                )

            else:
                id_julissa = usuario_existente.id_usuario

                print(
                    "El usuario inicial ya existe."
                )

            # Configuración inicial de empresa
            resultado_emp = await session.execute(
                select(Empresa).where(
                    Empresa.id == 1
                )
            )

            empresa_existente = resultado_emp.scalar_one_or_none()

            if not empresa_existente:
                nueva_empresa = Empresa(
                    nombre="Invernadero AgriSphere Local",
                    ubicacion="Tepic, Nayarit",
                    tamano_hectareas=15.5,
                    super_admin_id=id_julissa,
                    geocerca_latitud=21.5041,
                    geocerca_longitud=-104.8945,
                    geocerca_radio_metros=50
                )

                session.add(nueva_empresa)

                print(
                    "Configuración inicial de empresa creada."
                )

            else:
                print(
                    "La empresa principal ya existe."
                )

    print("Sembrado de datos completado.")


if __name__ == "__main__":
    asyncio.run(
        poblar_base_datos()
    )