import asyncio
import bcrypt
from sqlalchemy.future import select
from app.database import AsyncSessionLocal, engine
from app.auth.models import Base, Usuario, UserRole  # <--- Importamos su Enum

async def poblar_base_datos():
    print("🌱 Conectando a PostgreSQL y verificando tablas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas verificadas.")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            
            usuario_test = "julissa_rieg"
            query = select(Usuario).where(Usuario.usuario == usuario_test)
            resultado_usr = await session.execute(query)
            usuario_existente = resultado_usr.scalar_one_or_none()
            
            if not usuario_existente:
                print("🔐 Encriptando contraseña con Bcrypt nativo...")
                password_bytes = "lalala".encode('utf-8')
                sal = bcrypt.gensalt()
                hash_bytes = bcrypt.hashpw(password_bytes, sal)
                hash_seguro = hash_bytes.decode('utf-8')
                
                print("📝 Insertando usuario de prueba con el Enum correcto...")
                nuevo_usuario = Usuario(
                    nombre="Julissa Velazquez",
                    usuario=usuario_test,
                    contraseña=hash_seguro,
                    rol=UserRole.USUARIO  # <--- ¡Magia pura! Le damos el Enum de tu compa
                )
                session.add(nuevo_usuario)
                print(f"   + Usuario inyectado con éxito: Julissa Velazquez ({usuario_test})")
            else:
                print("   o El usuario de prueba ya existe en los registros.")
                
    print("🏁 ¡Sembrado de datos completado exitosamente!")

if __name__ == "__main__":
    asyncio.run(poblar_base_datos())