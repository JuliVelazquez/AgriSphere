from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    ubicacion: Mapped[str] = mapped_column(String, nullable=True)
    tamano_hectareas: Mapped[float] = mapped_column(Float, default=0.0)
    estado: Mapped[str] = mapped_column(String, default="Activo")
    rfc: Mapped[str] = mapped_column(String, nullable=True)
    estado_republica: Mapped[str] = mapped_column(String, nullable=True)
    fecha_inicio: Mapped[str] = mapped_column(String, nullable=True)
    logotipo: Mapped[str] = mapped_column(String, nullable=True)
    cultivos: Mapped[str] = mapped_column(String, nullable=True)

    # Parámetros de Geocerca (Para RH / Checador)
    geocerca_latitud: Mapped[float] = mapped_column(Float, nullable=True)
    geocerca_longitud: Mapped[float] = mapped_column(Float, nullable=True)
    geocerca_radio_metros: Mapped[int] = mapped_column(Integer, default=50) 

    # Nomenclatura Dinámica (Labels)
    label_invernadero: Mapped[str] = mapped_column(String, default="Invernadero")
    label_boli: Mapped[str] = mapped_column(String, default="Boli")
    label_zona1: Mapped[str] = mapped_column(String, default="Zona Sur")
    label_zona2: Mapped[str] = mapped_column(String, default="Zona Norte")
    label_seccion: Mapped[str] = mapped_column(String, default="Capilla")
    label_surco: Mapped[str] = mapped_column(String, default="Linea")

    # Relaciones
    super_admin_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    encargado_almacen_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)