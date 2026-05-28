from fastapi import FastAPI
from app.auth.router import router as auth_router

app = FastAPI(
    title="API de Gestión Agrícola e Inventario",
    version="1.0.0"
)

# Registrar las rutas de autenticación
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"status": "online", "proyecto": "Sistema Agrícola 2026"}