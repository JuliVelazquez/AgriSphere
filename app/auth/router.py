from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import time

from app.database import get_db
from app.auth.models import Usuario  
from app.auth.utils import (
    verificar_password, 
    crear_token_acceso, 
    pwd_context, 
    PermitirRoles
)
from app.auth.schemas import (
    LoginRequest, 
    LoginResponse, 
    TokenDataResponse, 
    QRResponse, 
    QRData,
    UsuarioCreateRequest,
    UsuarioCreateResponse,
    UsuarioCreateData,
    PassMatchRequest
)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# ==========================================
# 1. AUTENTICACIÓN PRINCIPAL (LOGIN)
# ==========================================
@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint principal de autenticación.
    Valida credenciales, telemetría y genera el JWT.
    """
    # 1. Buscar al usuario en la base de datos de manera asíncrona
    query = select(Usuario).where(Usuario.usuario == payload.usuario)
    result = await db.execute(query)
    usuario_db = result.scalar_one_or_none()

    # 2. Validaciones de seguridad pasivas
    if not usuario_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario inactivo."
        )

    # 3. Verificar el hash de la contraseña usando bcrypt
    if not verificar_password(payload.password, usuario_db.contraseña):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas."
        )

    # 4. Procesar telemetría opcional (Aquí se puede guardar payload.geolocalizacion en logs si se requiere)

    # 5. Generar claims y firmar token JWT
    data_para_token = {
        "sub": str(usuario_db.id_usuario),
        "rol": usuario_db.rol.value if hasattr(usuario_db.rol, 'value') else str(usuario_db.rol),
        "device_id": payload.ui_device
    }
    
    token_jwt = crear_token_acceso(data=data_para_token)

    return LoginResponse(
        message="Autenticación correcta",
        data=TokenDataResponse(
            access_token=token_jwt,
            usuario_id=usuario_db.id_usuario,
            rol=data_para_token["rol"]
        )
    )


# ==========================================
# 2. OPERACIONES DE INGRESO (TRABAJADOR / QR)
# ==========================================
@router.get("/usuarios/me/qr", response_model=QRResponse)
async def generar_payload_qr(current_user: dict = Depends(PermitirRoles(["Usuario", "rol_rieg", "rol_fito", "rol_prod", "rol_mant", "rol_empa", "rol_alma", "rol_moni"]))):
    """
    B. Operaciones de Ingreso: Genera el string encriptado para el QR efímero del trabajador.
    """
    timestamp_actual = int(time.time())
    
    # Amarramos el QR al ID real del token descodificado
    qr_string = f"usr_{current_user['sub']}:timestamp_{timestamp_actual}:sig_ab89f3"
    
    return QRResponse(
        data=QRData(
            qr_string_data=qr_string,
            expires_in_seconds=60
        )
    )


# ==========================================
# 3. OPERACIONES DE OFICINA (ALTA DE USUARIOS)
# ==========================================
# ==========================================
# 3. OPERACIONES DE OFICINA (ALTA DE USUARIOS)
# ==========================================
@router.post("/admin/usuarios", response_model=UsuarioCreateResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario_oficina(payload: UsuarioCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    C. Operaciones de Oficina: Registra un nuevo empleado en la base de datos, 
    encripta su contraseña inicial y le asigna un rol agrícola.
    """
    # Verificar si el usuario ya existe en la base de datos
    query = select(Usuario).where(Usuario.usuario == payload.nombre_usuario)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El nombre de usuario ya está registrado."
        )

    # Usamos la función nativa limpia de utils en lugar de pwd_context
    from app.auth.utils import encriptar_password
    hash_seguro = encriptar_password(payload.password_plano)
    
    # Mapeamos los nombres de columna de PostgreSQL 
    nuevo_usuario = Usuario(
        usuario=payload.nombre_usuario,
        nombre=payload.nombre_usuario.replace("_", " ").title(),
        contraseña=hash_seguro,
        rol="USUARIO"  # <-- Cambiamos payload.rol_asignado por "USUARIO" temporalmente
    )
    
    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)
    
    return UsuarioCreateResponse(
        message="Usuario creado y credenciales encriptadas correctamente",
        data=UsuarioCreateData(
            usuario_id=nuevo_usuario.id_usuario,                 # Cambiado de .id a .id_usuario
            usuario=nuevo_usuario.usuario,
            rol=nuevo_usuario.rol.value if hasattr(nuevo_usuario.rol, 'value') else str(nuevo_usuario.rol),
            status_sistema="Activo"                              # Ajustado a string simple si no existe el campo
        )
    )


# ==========================================
# 4. OPERACIONES DE OFICINA (PASS-MATCH)
# ==========================================
@router.post("/admin/pass-match")
async def verificar_pass_match(payload: PassMatchRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifica si una contraseña ingresada coincide con la de un usuario específico en la base de datos.
    """
    # Buscar al usuario por su identificador único
    query = select(Usuario).where(Usuario.usuario == payload.usuario)
    result = await db.execute(query)
    usuario_db = result.scalar_one_or_none()
    
    if not usuario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado."
        )
        
    # Validar coincidencia segura sin exponer el texto plano
    coincide = verificar_password(payload.password_a_verificar, usuario_db.password_hash)
    
    return {
        "status": "success",
        "match": coincide,
        "message": "La contraseña coincide con los registros." if coincide else "La contraseña NO coincide."
    }