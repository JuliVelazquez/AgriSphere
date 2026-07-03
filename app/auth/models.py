from sqlalchemy import Date, Integer, String, Enum, ForeignKey, JSON, DateTime, Boolean, Column, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from datetime import datetime
from app.database import Base
from app.modulos.empresa.models import MarcajeReloj

# Roles oficiales para el sistema
class UserRole(str, enum.Enum):
    USUARIO = "Usuario"
    JEFE_AREA = "Jefe Área"
    OFICINA = "Oficina"

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    usuario: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False) # ej. empleado_01
    correo: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    contraseña: Mapped[str] = mapped_column(String, nullable=False) # Contraseña encriptada
    rol: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USUARIO, nullable=False)

    # Relación 1:1 hacia el Expediente (uselist=False garantiza que sea uno a uno)
    expediente: Mapped["ExpedienteTrabajador"] = relationship(
        "ExpedienteTrabajador", 
        back_populates="usuario_seguridad", 
        uselist=False
    )

    marcajes: Mapped[list["MarcajeReloj"]] = relationship(
        "MarcajeReloj",
        back_populates="empleado"
    )
class ExpedienteTrabajador(Base):
    __tablename__ = "expedientes_trabajadores"

    id_expediente: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Llave foránea que conecta con la tabla de seguridad
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), unique=True)
    
    # Datos Operativos
    tipo_usuario: Mapped[str | None] = mapped_column(String, nullable=True)  # Empleado, Técnico, Visitante, Proveedor
    estatus: Mapped[str | None] = mapped_column(String, default="base", nullable=True)
    empresa_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Relación con tabla de empresas
    empresa: Mapped[str | None] = mapped_column(String, nullable=True)
    area_rol: Mapped[str | None] = mapped_column(String, nullable=True)
    actividad: Mapped[str | None] = mapped_column(String, nullable=True)
    access_level: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Guarda arreglos como ["semillero", "invernadero_b"]

    # Datos Personales
    curp: Mapped[str | None] = mapped_column(String(18), unique=True, index=True, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    contacto: Mapped[str | None] = mapped_column(String, nullable=True)  # Domicilio
    cp: Mapped[str | None] = mapped_column(String, nullable=True)

    # Salud y Políticas
    salud: Mapped[str | None] = mapped_column(String, nullable=True)
    acepta: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    historial: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    # Relación inversa hacia el modelo Usuario
    usuario_seguridad: Mapped["Usuario"] = relationship(
        "Usuario", 
        back_populates="expediente"
    )

    #  Nueva tabla para el registro de asistencias
class RegistroAsistencia(Base):
    __tablename__ = "registro_asistencias"

    id = Column(Integer, primary_key=True, index=True)
    
    # ID del trabajador que se leerá del QR
    worker_id = Column(Integer, nullable=False, index=True)
    
    # Captura fecha y hora exactas del registro de asistencia
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Almacena 'check-in' o 'check-out'
    event = Column(String, nullable=False)
    
    # Almacenará 'A tiempo', 'Retardo', o 'Justificado' para el reporte
    status = Column(String, nullable=False)

class PermisoAsistencia(Base):
    __tablename__ = "permisos_asistencia"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, index=True, nullable=False)
    fecha_permiso = Column(Date, nullable=False)
    motivo = Column(String, nullable=False) # Ej: "Enfermedad", "Vacaciones", "Asunto Familiar"
    registrado_en = Column(DateTime(timezone=True), server_default=func.now())

class Invernadero(Base):
    __tablename__ = "invernaderos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)          # ej. INV-01
    cultivo = Column(String, nullable=True)          # ej. Tomates
    id_ciclo = Column(String, nullable=True)         # ej. 1.2-26
    superficie_m2 = Column(Float, nullable=True)     # ej. 10000
    fecha_plantacion = Column(DateTime, nullable=True)
    estado = Column(String, default="Activo")        # Activo, Alerta, Inactivo
    ultima_revision = Column(DateTime, nullable=True)
    responsable = Column(String, nullable=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)

class MonitoreoPlagas(Base):
    __tablename__ = "monitoreos_plagas"

    id = Column(Integer, primary_key=True, index=True)
    invernadero_id = Column(Integer, ForeignKey("invernaderos.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    plagas_detectadas = Column(Integer, default=0)      # ej. 142
    insectos_beneficos = Column(Integer, default=0)     # ej. 8450
    focos_enfermedad = Column(Integer, default=0)       # ej. 3
    nivel_alerta = Column(String, default="NORMAL")     # NORMAL, ALTO, CRITICO
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    notas = Column(String, nullable=True)

class PlantaRetirada(Base):
    __tablename__ = "plantas_retiradas"

    id = Column(Integer, primary_key=True, index=True)
    invernadero_id = Column(Integer, ForeignKey("invernaderos.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    tipo_problema = Column(String, nullable=False)   # ej. Fusarium, Botrytis, Daño Mecánico
    cantidad = Column(Integer, default=0)            # ej. 45
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

class RecuperacionPassword(Base):
    __tablename__ = "recuperacion_password"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    codigo_otp = Column(String, nullable=False)        # el código de 6 dígitos
    reset_token = Column(String, nullable=True)        # se genera después de verificar el OTP
    usado = Column(Boolean, default=False)             # para invalidarlo después de usarlo
    expires_at = Column(DateTime(timezone=True), nullable=False)  # caduca en 15 minutos
    creado_en = Column(DateTime(timezone=True), server_default=func.now())