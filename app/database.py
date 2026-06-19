from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Crea el motor asíncrono conectado a tu Postgres (agrisphere)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Muestra el SQL ejecutado en la terminal
)

# Crea la fábrica de sesiones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Clase base para mapear las futuras tablas
class Base(DeclarativeBase):
    pass

#  Dependencia para los endpoints de FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session