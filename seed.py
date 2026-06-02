import asyncio
import bcrypt
from sqlalchemy.future import select
from app.database import AsyncSessionLocal, engine
from app.auth.models import Base, Usuario, UserRole
from app.modulos.empresa.models import Empresa  # <--- Importamos tu nuevo modelo

async def poblar_base_datos():
    print("🌱 Conectando a PostgreSQL y verificando tablas...")
    # Al importar 'Empresa' arriba, esta línea automáticamente creará la nueva tabla
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas verificadas/creadas.")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            
            # --- 1. SECCIÓN DE USUARIOS ---
            usuario_test = "julissa_rieg"
            query_usr = select(Usuario).where(Usuario.usuario == usuario_test)
            resultado_usr = await session.execute(query_usr)
            usuario_existente = resultado_usr.scalar_one_or_none()
            
            if not usuario_existente:
                password_bytes = "lalala".encode('utf-8')
                sal = bcrypt.gensalt()
                hash_bytes = bcrypt.hashpw(password_bytes, sal)
                
                nuevo_usuario = Usuario(
                    nombre="Julissa Velazquez",
                    usuario=usuario_test,
                    contraseña=hash_bytes.decode('utf-8'),
                    rol=UserRole.USUARIO
                )
                session.add(nuevo_usuario)
                await session.flush() # Para que nos genere su ID de inmediato
                id_julissa = nuevo_usuario.id_usuario
                print(f"   + Usuario inyectado con éxito: {usuario_test}")
            else:
                id_julissa = usuario_existente.id_usuario
                print("   o El usuario de prueba ya existe.")

            # --- 2. SECCIÓN DE EMPRESA ---
            query_emp = select(Empresa).where(Empresa.id == 1)
            resultado_emp = await session.execute(query_emp)
            empresa_existente = resultado_emp.scalar_one_or_none()

            if not empresa_existente:
                print("Creando la configuración inicial de la Empresa...")
                nueva_empresa = Empresa(
                    nombre="AgroCorp Demo",
                    ubicacion="Tepic, Nayarit",
                    tamano_hectareas=15.5,
                    super_admin_id=id_julissa # Asignamos a Julissa como admin temporalmente
                )
                session.add(nueva_empresa)
                print("   + Empresa generada con éxito.")
            else:
                print("   o La empresa principal ya existe en los registros.")
                
    print("🏁 ¡Sembrado de datos completado exitosamente!")

if __name__ == "__main__":
    asyncio.run(poblar_base_datos())