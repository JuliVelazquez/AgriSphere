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
    contraseña: Mapped[str] = mapped_column(String, nullable=False) # Contraseña encriptada
    rol: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USUARIO, nullable=False)
    correo: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
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
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
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

class RecuperacionPassword(Base):
    __tablename__ = "recuperacion_password"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    codigo_otp = Column(String, nullable=False)        # el código de 6 dígitos
    reset_token = Column(String, nullable=True)        # se genera después de verificar el OTP
    usado = Column(Boolean, default=False)             # para invalidarlo después de usarlo
    expires_at = Column(DateTime(timezone=True), nullable=False)  # caduca en 15 minutos
    creado_en = Column(DateTime(timezone=True), server_default=func.now())