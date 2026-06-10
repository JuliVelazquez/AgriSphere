from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, cast, Date
from datetime import datetime, date, time, timedelta
from typing import Optional

from app.database import get_db
from app.auth.models import Usuario, ExpedienteTrabajador, RegistroAsistencia
from app.modulos.empresa.models import Empresa
from app.auth.utils import (
    verificar_password, 
    crear_token_acceso, 
    PermitirRoles,
    encriptar_password,  #---> Importamos la función de utils para encriptar contraseñas
    calcular_distancia_metros  #--> Importamos la función para calcular distancia entre coordenadas
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
    PassMatchRequest,
    TrabajadorCreate,  #--> Esquema para la creación de trabajadores desde Recursos Humanos, que incluye datos para ambas tablas (usuarios y expedientes_trabajadores)
    EmpresaConfig,
    AsistenciaRegistrarRequest,
    ReporteAsistenciaResponse
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

    # 4. Procesar telemetría opcional y Validación de Geo-cerca
    if payload.ui_device == "app_movil":
        if not payload.ubicacion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Se requiere ubicación GPS activa para acceder desde la aplicación móvil."
            )

        # Coordenadas maestras de la empresa (Después leeremos el de la BD, por ahora usamos Tepic)
        LAT_EMPRESA = 21.5041
        LON_EMPRESA = -104.8945
        RADIO_PERMITIDO = 50.0  # El trabajador debe estar a menos de 50 metros
        
        distancia = calcular_distancia_metros(
            payload.ubicacion.latitud,
            payload.ubicacion.longitud,
            LAT_EMPRESA,
            LON_EMPRESA
        )

        if distancia > RADIO_PERMITIDO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Estás a {int(distancia)} metros del Invernadero. Acércate a la zona de trabajo."
            )

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

@router.post("/trabajador", status_code=201)
async def registrar_trabajador(payload: TrabajadorCreate, db: AsyncSession = Depends(get_db)):
    """
    ### Alta de Trabajador y Expediente (Recursos Humanos)
    Recibe el payload masivo, divide la información para proteger las credenciales
    y almacena el expediente operativo del trabajador.
    """
    # 1. Encriptar la contraseña de forma segura (usando ==implementación nativa)
    hashed_password = encriptar_password(payload.contraseña)
    
    # 2. Crear el registro en la tabla de Seguridad ('usuarios')
    nuevo_usuario = Usuario(
        nombre=payload.nombre_completo,
        usuario=payload.nombre_usuario,
        contraseña=hashed_password,
        rol=payload.rol_asignado
    )
    
    db.add(nuevo_usuario)
    # Hacemos un flush para que PostgreSQL le asigne un ID al usuario sin cerrar la transacción
    await db.flush() 
    
    # 3. Crear el registro en la tabla de Recursos Humanos ('expedientes_trabajadores')
    nuevo_expediente = ExpedienteTrabajador(
        usuario_id=nuevo_usuario.id_usuario, # Aquí usamos el ID recién generado
        tipo_usuario=payload.expediente.tipo_usuario,
        estatus=payload.expediente.estatus,
        empresa_id=payload.expediente.empresa_id,
        empresa=payload.expediente.empresa,
        area_rol=payload.expediente.area_rol,
        actividad=payload.expediente.actividad,
        access_level=payload.expediente.access_level,
        curp=payload.expediente.curp,
        telefono=payload.expediente.telefono,
        email=payload.expediente.email,
        contacto=payload.expediente.contacto,
        cp=payload.expediente.cp,
        salud=payload.expediente.salud,
        acepta=payload.expediente.acepta,
        historial=payload.expediente.historial
    )
    
    db.add(nuevo_expediente)
    
    # 4. Confirmar los cambios en ambas tablas al mismo tiempo
    await db.commit()
    
    return {
        "status": "success",
        "message": "Trabajador y expediente creados correctamente",
        "data": {
            "usuario_id": nuevo_usuario.id_usuario,
            "usuario": nuevo_usuario.usuario
        }
    }

# ==========================================
# CONFIGURACIÓN DE EMPRESA (GEOCERCA)
# ==========================================
@router.post("/empresa/parametros", summary="Configurar parámetros y Geocerca")
async def configurar_empresa(payload: EmpresaConfig, db: AsyncSession = Depends(get_db)):
    """
    Recibe los datos desde la vista de TI/RH para configurar 
    las coordenadas centrales y el radio de tolerancia del invernadero.
    """
    # 1. Buscamos si ya existe una configuración guardada
    query = select(Empresa).limit(1)
    result = await db.execute(query)
    empresa_db = result.scalar_one_or_none()

    if empresa_db:
        # 2A. Si ya existe, actualizamos usando los nombres reales de tu BD
        empresa_db.nombre = payload.nombre
        empresa_db.geocerca_latitud = payload.geocerca_latitud
        empresa_db.geocerca_longitud = payload.geocerca_longitud
        empresa_db.geocerca_radio_metros = payload.geocerca_radio_metros
        mensaje = "Parámetros y geocerca actualizados correctamente."
    else:
        # 2B. Si no existe, creamos el registro
        nueva_empresa = Empresa(
            nombre=payload.nombre,
            geocerca_latitud=payload.geocerca_latitud,
            geocerca_longitud=payload.geocerca_longitud,
            geocerca_radio_metros=payload.geocerca_radio_metros
        )
        db.add(nueva_empresa)
        mensaje = "Parámetros de empresa creados por primera vez."

    await db.commit()
    
    return {
        "status": "success",
        "message": mensaje,
        "data": payload.model_dump()
    }

# ==========================================
# CONFIGURACIÓN DE REGISTRO DE ASISTENCIA
# ==========================================

@router.post("/asistencia/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_asistencia(
    request: AsistenciaRegistrarRequest, 
    db: AsyncSession = Depends(get_db)
):
    hoy = date.today()
    
    # Busca el último registro de asistencia del trabajador de hoy
    stmt = (
        select(RegistroAsistencia)
        .where(
            RegistroAsistencia.worker_id == request.worker_id,
            RegistroAsistencia.timestamp >= datetime.combine(hoy, time.min)
        )
        .order_by(desc(RegistroAsistencia.timestamp))
        .limit(1)
    )
    
    result = await db.execute(stmt)
    ultimo_registro = result.scalar_one_or_none()
    
    # Si no ha checado hoy o el último movimiento fue una salida, se marca entrada
    if ultimo_registro is None or ultimo_registro.event == "check-out":
        nuevo_evento = "check-in"
    else:
        nuevo_evento = "check-out"
        
    # Se define la hora de entrada permitida
    hora_actual = datetime.now().time()
    hora_limite_entrada = time(9, 0)  # 09:00 AM
    
    if nuevo_evento == "check-in":
        if hora_actual > hora_limite_entrada:
            nuevo_status = "Retardo"
        else:
            nuevo_status = "A tiempo"
    else:
        # Para las salidas (check-out) se marca "A tiempo"
        nuevo_status = "A tiempo"
        
    # 4. Guardado en la base de datos
    nuevo_registro = RegistroAsistencia(
        worker_id=request.worker_id,
        event=nuevo_evento,
        status=nuevo_status
    )
    
    try:
        db.add(nuevo_registro)
        await db.commit()
        await db.refresh(nuevo_registro)
        
        # 5. Respuesta exitosa a mostrar en la app del encargado
        return {
            "status": "success",
            "message": f"Registro de {nuevo_evento} guardado correctamente",
            "data": {
                "worker_id": nuevo_registro.worker_id,
                "event": nuevo_registro.event,
                "status": nuevo_registro.status,
                "timestamp": nuevo_registro.timestamp
            }
        }
        # Respuesta de error en caso de que falle la base de datos
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error crítico al guardar la asistencia: {str(e)}"
        )
    
@router.get("/asistencia/reporte", response_model=ReporteAsistenciaResponse)
async def obtener_reporte_asistencia(
    fecha_inicio: date,
    fecha_fin: date,
    worker_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    # 1. Traer los registros (busca un día extra por si el UTC saltó el día)
    stmt = select(RegistroAsistencia).where(
        cast(RegistroAsistencia.timestamp, Date) >= fecha_inicio,
        cast(RegistroAsistencia.timestamp, Date) <= fecha_fin + timedelta(days=1)
    )
    
    if worker_id:
        stmt = stmt.where(RegistroAsistencia.worker_id == worker_id)
        
    stmt = stmt.order_by(RegistroAsistencia.worker_id, RegistroAsistencia.timestamp)
    result = await db.execute(stmt)
    registros = result.scalars().all()

    # 2. Agrupación y Ajuste Maestro de Zona Horaria
    agrupados = defaultdict(lambda: defaultdict(list))
    for r in registros:
        # Forzamos el reloj a la hora local (-7 horas)
        timestamp_local = r.timestamp - timedelta(hours=7)
        dia = timestamp_local.date()
        
        if fecha_inicio <= dia <= fecha_fin:
            # Sobreescribimos la hora del registro en memoria para que trabaje con la hora local
            r.timestamp = timestamp_local
            agrupados[r.worker_id][dia].append(r)

    # 3. Asumiendo horario de 9 a 5
    HORA_ENTRADA = time(9, 0)
    HORA_SALIDA = time(17, 0)
    reporte_final = []

    # 4. Calcular día por día
    for w_id, dias in agrupados.items():
        for dia, movimientos in dias.items():
            movimientos.sort(key=lambda x: x.timestamp)
            
            primer_check_in = next((m for m in movimientos if m.event == "check-in"), None)
            ultimo_check_out = next((m for m in reversed(movimientos) if m.event == "check-out"), None)

            min_retardo = 0
            min_salida_ant = 0
            horas_totales = 0.0
            horas_ordinarias = 0.0
            horas_extra = 0.0

            if primer_check_in:
                t_in = primer_check_in.timestamp.time()
                if t_in > HORA_ENTRADA:
                    dt_in = datetime.combine(dia, t_in)
                    dt_entrada = datetime.combine(dia, HORA_ENTRADA)
                    min_retardo = int((dt_in - dt_entrada).total_seconds() / 60)

            if ultimo_check_out:
                t_out = ultimo_check_out.timestamp.time()
                if t_out < HORA_SALIDA:
                    dt_out = datetime.combine(dia, t_out)
                    dt_salida = datetime.combine(dia, HORA_SALIDA)
                    min_salida_ant = int((dt_salida - dt_out).total_seconds() / 60)

            if primer_check_in and ultimo_check_out:
                delta = ultimo_check_out.timestamp - primer_check_in.timestamp
                horas_totales = round(delta.total_seconds() / 3600, 2)
                
                horas_ordinarias = min(8.0, horas_totales)
                horas_extra = max(0.0, horas_totales - 8.0)

            reporte_final.append({
                "fecha": dia,
                "worker_id": w_id,
                "minutos_retardo": min_retardo,
                "minutos_salida_anticipada": min_salida_ant,
                "horas_totales": horas_totales,
                "horas_ordinarias": horas_ordinarias,
                "horas_extra": horas_extra
            })

    return {
        "status": "success",
        "data": reporte_final
    }