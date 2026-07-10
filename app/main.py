from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.auth.router import router as auth_router
from app.modulos.empresa.router import router as empresa_router 
from app.database import engine, Base
from app.modulos.empresa.models import Empresa 
from app.auth.models import Usuario, ExpedienteTrabajador
from app.modulos.dashboard.router import router as dashboard_router

# manejo de inicio y apagado del servidor para crear tablas automáticamente
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al iniciar el servidor, se crean las tablas en la base de datos si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
# ----------------------------------------------------

# Le pasamos el lifespan a la aplicación
app = FastAPI(
    title="API de Gestión Agrícola e Inventario",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/agrisphere"
)

# Registrar las rutas
app.include_router(auth_router)
app.include_router(empresa_router) 
app.include_router(dashboard_router)

@app.get("/")
async def root():
    return {"status": "online", "proyecto": "Sistema Agrícola 2026"}