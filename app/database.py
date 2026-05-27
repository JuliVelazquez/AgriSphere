from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# 1. Crear el motor asíncrono conectado a tu Postgres (agrisphere)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Muestra el SQL ejecutado en la terminal (súper útil para desarrollo)
)

# 2. Crear la fábrica de sesiones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 3. Clase base para mapear las futuras tablas
class Base(DeclarativeBase):
    pass

# 4. Dependencia para los endpoints de FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session