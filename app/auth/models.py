from sqlalchemy import Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum
from app.database import Base

# Roles oficiales de tu diseño AgriSphere
class UserRole(str, enum.Enum):
    USUARIO = "Usuario"
    JEFE_AREA = "Jefe Área"
    OFICINA = "Oficina"

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    usuario: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False) # ej. empleado_01
    contraseña: Mapped[str] = mapped_column(String, nullable=False) # Contraseña encriptada por passlib
    rol: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USUARIO, nullable=False)