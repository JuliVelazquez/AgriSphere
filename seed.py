import asyncio
import hashlib
import base64
import bcrypt
from sqlalchemy.future import select
from app.database import AsyncSessionLocal, engine
from app.auth.models import Base, Usuario, UserRole

async def poblar_base_datos():
    print("Conectando a PostgreSQL y verificando tablas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablas verificadas.")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            
            usuario_test = "julissa_rieg"
            query = select(Usuario).where(Usuario.usuario == usuario_test)
            resultado_usr = await session.execute(query)
            usuario_existente = resultado_usr.scalar_one_or_none()
            
            if not usuario_existente:
                print("Encriptando contraseña simulando el esquema oficial de passlib...")
                
                # 1. Simular el comportamiento de bcrypt_sha256 de passlib para evitar errores de verificación
                password_puro = "lalala"
                sha256_hash = hashlib.sha256(password_puro.encode('utf-8')).digest()
                
                # RESTRICCIÓN: Passlib usa Base64 estándar pero remueve el padding (=)
                sha256_b64 = base64.b64encode(sha256_hash).decode('utf-8').rstrip('=')
                
                # 2. Aplicar el Bcrypt clásico sobre el string codificado
                sal = bcrypt.gensalt(rounds=12)
                hash_bytes = bcrypt.hashpw(sha256_b64.encode('utf-8'), sal)
                hash_seguro = hash_bytes.decode('utf-8')
                
                print("Insertando usuario de prueba...")
                nuevo_usuario = Usuario(
                    nombre="Julissa Velazquez",
                    usuario=usuario_test,
                    contraseña=hash_seguro,
                    rol=UserRole.USUARIO
                )
                session.add(nuevo_usuario)
                print(f"   + Usuario inyectado con éxito: {nuevo_usuario.nombre} ({usuario_test})")
                print("   o El usuario de prueba ya existe en los registros.")
                
    print("¡Sembrado de datos completado exitosamente!")

if __name__ == "__main__":
    asyncio.run(poblar_base_datos())