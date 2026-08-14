from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc, cast, update, Date
from datetime import datetime, date, time, timedelta, timezone
import time as time_module
from typing import Optional
import random
from app.utils.qr_security import generar_firma_qr

# 1. Base de datos
from app.database import get_db

# 2. Modelos
from app.auth.models import (
    Usuario, 
    ExpedienteTrabajador, 
    RegistroAsistencia, 
    PermisoAsistencia,
    RecuperacionPassword
)
from app.modulos.empresa.models import Empresa

# 3. Utilidades
from app.auth.utils import (
    crear_token_reset,
    verificar_password, 
    crear_token_acceso, 
    PermitirRoles,
    encriptar_password,
    calcular_distancia_metros,
    decodificar_token
)

# 4. Esquemas
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
    TrabajadorCreate,
    EmpresaConfig,
    AsistenciaRegistrarRequest,
    ReporteAsistenciaResponse,
    PermisoCreateRequest,
    PermisoResponse,
    PerfilEmpleadoResponse,  
    PerfilEmpleadoData,
    RecuperarPasswordRequest,
    RecuperarPasswordResponse,
    VerificarCodigoRequest,     
    VerificarCodigoResponse,
    ResetPasswordRequest, 
    ResetPasswordResponse,
    EmpleadoListaItem,
    ListaEmpleadosResponse
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

    # 4. Procesar telemetría opcional y validación de geocerca
    if payload.ui_device == "app_movil":

        if not payload.ubicacion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Se requiere ubicación GPS activa "
                    "para acceder desde la aplicación móvil."
                )
            )

        # Consultar la geocerca configurada en PostgreSQL
        resultado_empresa = await db.execute(
            select(Empresa).limit(1)
        )

        empresa_db = resultado_empresa.scalar_one_or_none()

        if not empresa_db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "No existe una geocerca configurada "
                    "para la empresa."
                )
            )

        lat_empresa = empresa_db.geocerca_latitud
        lon_empresa = empresa_db.geocerca_longitud
        radio_permitido = empresa_db.geocerca_radio_metros

        distancia = calcular_distancia_metros(
            payload.ubicacion.latitud,
            payload.ubicacion.longitud,
            lat_empresa,
            lon_empresa
        )

        if distancia > radio_permitido:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado. Estás a "
                    f"{int(distancia)} metros del Invernadero. "
                    f"Acércate a la zona de trabajo."
                )
            )

    # 5. Generar claims y firmar token JWT
    data_para_token = {
        "sub": str(usuario_db.id_usuario),
        "rol": (
            usuario_db.rol.value
            if hasattr(usuario_db.rol, "value")
            else str(usuario_db.rol)
        ),
        "device_id": payload.ui_device
    }

    token_jwt = crear_token_acceso(
        data=data_para_token
    )

    # 6. Retornar respuesta final
    return LoginResponse(
        message="Autenticación correcta",
        data=TokenDataResponse(
            access_token=token_jwt,
            token_type="bearer",
            usuario_id=usuario_db.id_usuario,
            rol=data_para_token["rol"]
        )
    )

# ==========================================
# 2. OPERACIONES DE INGRESO (TRABAJADOR / QR)
# ==========================================

@router.get("/usuarios/me/qr", response_model=QRResponse)
async def generar_payload_qr(
    latitud: float,
    longitud: float,
    current_user: dict = Depends(
        PermitirRoles([
            "Usuario"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera el QR efímero del trabajador únicamente
    si se encuentra dentro de la geocerca configurada.
    """

    # 1. Consultar la geocerca de la empresa
    resultado_empresa = await db.execute(
        select(Empresa).limit(1)
    )

    empresa_db = resultado_empresa.scalar_one_or_none()

    if not empresa_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No existe una geocerca configurada para la empresa."
        )

    if (
        empresa_db.geocerca_latitud is None
        or empresa_db.geocerca_longitud is None
        or empresa_db.geocerca_radio_metros is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La geocerca de la empresa está incompleta."
        )

    # 2. Calcular distancia del trabajador a la empresa
    distancia = calcular_distancia_metros(
        latitud,
        longitud,
        float(empresa_db.geocerca_latitud),
        float(empresa_db.geocerca_longitud)
    )

    radio_permitido = float(
        empresa_db.geocerca_radio_metros
    )

    # 3. Bloquear generación fuera de la geocerca
    if distancia > radio_permitido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"No puedes generar tu código QR fuera "
                f"del área de trabajo. Estás a "
                f"{int(distancia)} metros del invernadero."
            )
        )

    # 4. Generar QR efímero
    timestamp_actual = int(
        time_module.time()
    )

    usuario_id = int(
        current_user["sub"]
    )

    firma = generar_firma_qr(
        usuario_id=usuario_id,
        timestamp=timestamp_actual
    )

    qr_string = (
        f"usr_{usuario_id}:"
        f"timestamp_{timestamp_actual}:"
        f"sig_{firma}"
    )

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
        rol=payload.rol_asignado,
        correo=payload.datos_contacto.email if payload.datos_contacto else None,
        telefono=payload.datos_contacto.telefono if payload.datos_contacto else None
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
    coincide = verificar_password(
    payload.password_a_verificar,
    usuario_db.contraseña
    )
    
    return {
        "status": "success",
        "match": coincide,
        "message": "La contraseña coincide con los registros." if coincide else "La contraseña NO coincide."
    }


@router.post("/trabajador", status_code=201)
async def registrar_trabajador(
    payload: TrabajadorCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar que el nombre de usuario no exista
    resultado_usuario = await db.execute(
        select(Usuario).where(
            Usuario.usuario == payload.nombre_usuario
        )
    )

    if resultado_usuario.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario ya está registrado."
        )

    # 2. Verificar que la CURP no exista
    if payload.expediente.curp:
        resultado_curp = await db.execute(
            select(ExpedienteTrabajador).where(
                ExpedienteTrabajador.curp == payload.expediente.curp
            )
        )

        if resultado_curp.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="La CURP ya está registrada."
            )

    try:
        # 3. Encriptar la contraseña de forma segura (usando ==implementación nativa)
        hashed_password = encriptar_password(payload.contraseña)

        # 4. Crear el registro en la tabla de Seguridad ('usuarios')
        nuevo_usuario = Usuario(
            nombre=payload.nombre_completo,
            usuario=payload.nombre_usuario,
            contraseña=hashed_password,
            rol=payload.rol_asignado,
            correo=payload.expediente.email if payload.expediente else None,
            telefono=payload.expediente.telefono if payload.expediente else None
        )

        db.add(nuevo_usuario)

        # Hacemos un flush para que PostgreSQL le asigne un ID al usuario sin cerrar la transacción
        await db.flush()

        # 5. # 3. Crear el registro en la tabla de Recursos Humanos ('expedientes_trabajadores')
        nuevo_expediente = ExpedienteTrabajador(
            usuario_id=nuevo_usuario.id_usuario,
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

        # 6. Confirmar los cambios en ambas tablas al mismo tiempo
        await db.commit()

        return {
            "status": "success",
            "message": "Trabajador y expediente creados correctamente",
            "data": {
                "usuario_id": nuevo_usuario.id_usuario,
                "usuario": nuevo_usuario.usuario
            }
        }

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Ya existe un registro con alguno de los datos únicos proporcionados."
        )

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al registrar al trabajador."
        )
    

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
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
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
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
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

            # Verificamos si existe un permiso para este trabajador en este día
            query_permiso = select(PermisoAsistencia).where(
                PermisoAsistencia.worker_id == w_id,
                PermisoAsistencia.fecha_permiso == dia
            )
            res_permiso = await db.execute(query_permiso)
            existe_permiso = res_permiso.scalars().first() is not None

            min_retardo = 0
            min_salida_ant = 0
            horas_totales = 0.0
            horas_ordinarias = 0.0
            horas_extra = 0.0

            if existe_permiso:
                min_retardo = 0
                min_salida_ant = 0

            else:

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

@router.post("/permisos", response_model=PermisoResponse)
async def registrar_permiso(
    request: PermisoCreateRequest,
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    # Creamos el objeto con los datos que llegan de la petición
    nuevo_permiso = PermisoAsistencia(
        worker_id=request.worker_id,
        fecha_permiso=request.fecha_permiso,
        motivo=request.motivo
    )
        
    # Guardamos en PostgreSQL
    db.add(nuevo_permiso)
    await db.commit()
        
    return {
        "status": "success",
        "message": f"Permiso por '{request.motivo}' registrado exitosamente para el trabajador {request.worker_id}."
        }

#endpoint de empleados
@router.get(
    "/empleados",
    response_model=ListaEmpleadosResponse
)
async def listar_empleados(
    current_user: dict = Depends(
        PermitirRoles([
            "Jefe Área",
            "Oficina"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    resultado = await db.execute(
        select(
            Usuario,
            ExpedienteTrabajador
        )
        .join(
            ExpedienteTrabajador,
            ExpedienteTrabajador.usuario_id
            == Usuario.id_usuario
        )
        .order_by(Usuario.nombre)
    )

    filas = resultado.all()

    empleados = []

    for usuario, expediente in filas:

        rol_texto = (
            usuario.rol.value
            if hasattr(usuario.rol, "value")
            else str(usuario.rol)
        )

        rol_comparacion = (
            rol_texto
            .strip()
            .lower()
            .replace("_", " ")
        )

        # No mostramos supervisores ni personal
        # administrativo como trabajadores.
        if rol_comparacion in {
            "oficina",
            "jefe área",
            "jefe area",
            "administrador"
        }:
            continue

        empleados.append(
            EmpleadoListaItem(
                id_empleado=usuario.id_usuario,
                nombre_completo=usuario.nombre,
                rol=rol_texto,
                departamento=expediente.area_rol,
                estatus=expediente.estatus
            )
        )

    return ListaEmpleadosResponse(
        data=empleados
    )

@router.get("/empleados/me", response_model=PerfilEmpleadoResponse)
async def obtener_perfil_empleado(
    current_user: dict = Depends(
        PermitirRoles([
            "Usuario",
            "Jefe Área",
            "Oficina"
        ])
    ),
    db: AsyncSession = Depends(get_db)
):
    usuario_id = int(current_user["sub"])

    # 1. Buscar datos del usuario
    resultado = await db.execute(
        select(Usuario).where(Usuario.id_usuario == usuario_id)
    )
    usuario = resultado.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Buscar expediente para obtener área/departamento
    resultado_exp = await db.execute(
        select(ExpedienteTrabajador).where(ExpedienteTrabajador.usuario_id == usuario_id)
    )
    expediente = resultado_exp.scalar_one_or_none()

    # 3. Generar el string del QR
    import time as time_module
    timestamp_actual = int(time_module.time())
    qr_string = f"usr_{usuario_id}:timestamp_{timestamp_actual}:sig_ab89f3"

    return PerfilEmpleadoResponse(
        data=PerfilEmpleadoData(
            id_empleado=usuario_id,
            nombre_completo=usuario.nombre,
            rol=usuario.rol.value if hasattr(usuario.rol, 'value') else str(usuario.rol),
            departamento=expediente.area_rol if expediente else None,
            nombre_supervisor=None,  # se puede agregar después cuando haya supervisores
            fecha_hora_servidor=datetime.now(),
            qr_string=qr_string
        )
    )
@router.post("/recuperar-password", response_model=RecuperarPasswordResponse)
async def solicitar_recuperacion(
    payload: RecuperarPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Buscar usuario por correo
    resultado = await db.execute(
        select(Usuario).where(Usuario.correo == payload.correo)
    )
    usuario = resultado.scalar_one_or_none()

    # 2. Si no existe, respondemos igual por seguridad (no revelamos si existe o no)
    if not usuario:
        return RecuperarPasswordResponse()

    # 3. Generar código OTP de 6 dígitos
    codigo = str(random.randint(100000, 999999))

    # 4. Calcular expiración (15 minutos)
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=15)

    # 5. Guardar en la base de datos
    nuevo_otp = RecuperacionPassword(
        usuario_id=usuario.id_usuario,
        codigo_otp=codigo,
        usado=False,
        expires_at=expiracion
    )
    db.add(nuevo_otp)
    await db.commit()

    # 6. Envio por correo
    print(f"[SIMULACIÓN EMAIL] Código OTP para {payload.correo}: {codigo}")

    return RecuperarPasswordResponse()

@router.post(
    "/verificar-codigo",
    response_model=VerificarCodigoResponse
)
async def verificar_codigo_otp(
    payload: VerificarCodigoRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Buscar usuario
    resultado = await db.execute(
        select(Usuario).where(
            Usuario.correo == payload.correo
        )
    )
    usuario = resultado.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado."
        )

    # 2. Buscar el OTP más reciente sin utilizar
    resultado_otp = await db.execute(
        select(RecuperacionPassword)
        .where(
            RecuperacionPassword.usuario_id
            == usuario.id_usuario,
            RecuperacionPassword.codigo_otp
            == payload.codigo_otp,
            RecuperacionPassword.usado.is_(False),
            RecuperacionPassword.expires_at
            > datetime.now(timezone.utc)
        )
        .order_by(
            desc(RecuperacionPassword.creado_en)
        )
        .limit(1)
    )

    otp = resultado_otp.scalar_one_or_none()

    if not otp:
        raise HTTPException(
            status_code=400,
            detail="Código inválido, expirado o utilizado anteriormente."
        )

    reset_token = crear_token_reset(
        usuario_id=usuario.id_usuario,
        otp_id=otp.id
    )

    try:
        # Invalidar todos los registros que tengan ese mismo código
        await db.execute(
            update(RecuperacionPassword)
            .where(
                RecuperacionPassword.usuario_id
                == usuario.id_usuario,
                RecuperacionPassword.codigo_otp
                == payload.codigo_otp,
                RecuperacionPassword.usado.is_(False)
            )
            .values(usado=True)
        )

        # Guardar el token en el registro seleccionado
        await db.execute(
            update(RecuperacionPassword)
            .where(
                RecuperacionPassword.id == otp.id
            )
            .values(reset_token=reset_token)
        )

        await db.commit()

    except Exception as error:
        await db.rollback()
        print("ERROR AL VERIFICAR OTP:", error)

        raise HTTPException(
            status_code=500,
            detail="No fue posible verificar el código."
        )

    return VerificarCodigoResponse(
        reset_token=reset_token
    )

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Decodificar token
    try:
        datos_token = decodificar_token(
            payload.reset_token
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="El token ha expirado o es inválido."
        )

    usuario_id = datos_token.get("sub")
    tipo_token = datos_token.get("tipo")
    otp_id = datos_token.get("otp_id")

    if not usuario_id or not otp_id:
        raise HTTPException(
            status_code=400,
            detail="Token incompleto o inválido."
        )

    if tipo_token != "reset_password":
        raise HTTPException(
            status_code=400,
            detail="El token no sirve para restablecer contraseñas."
        )

    nueva_contraseña = encriptar_password(
        payload.nueva_password
    )

    try:
        # 2. Consumir el token
        resultado_token = await db.execute(
            update(RecuperacionPassword)
            .where(
                RecuperacionPassword.id == int(otp_id),
                RecuperacionPassword.usuario_id
                == int(usuario_id),
                RecuperacionPassword.reset_token
                == payload.reset_token
            )
            .values(reset_token=None)
            .returning(RecuperacionPassword.id)
        )

        token_consumido = (
            resultado_token.scalar_one_or_none()
        )

        if token_consumido is None:
            await db.rollback()

            raise HTTPException(
                status_code=400,
                detail=(
                    "Token inválido, no encontrado "
                    "o utilizado anteriormente."
                )
            )

        # 3. Actualizar contraseña directamente
        resultado_usuario = await db.execute(
            update(Usuario)
            .where(
                Usuario.id_usuario == int(usuario_id)
            )
            .values({
                Usuario.contraseña: nueva_contraseña
            })
            .returning(Usuario.id_usuario)
        )

        usuario_actualizado = (
            resultado_usuario.scalar_one_or_none()
        )

        if usuario_actualizado is None:
            await db.rollback()

            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado."
            )

        # Token y contraseña se guardan juntos
        await db.commit()

    except HTTPException:
        raise

    except Exception as error:
        await db.rollback()

        print(
            "ERROR AL RESTABLECER CONTRASEÑA:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible actualizar la contraseña."
        )

    return ResetPasswordResponse()