from sqlalchemy import Integer, Date, ForeignKey, String, Float, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from app.database import Base 

class ReporteMonitoreo(Base):
    __tablename__ = "reportes_monitoreo"

    id_reporte: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha_registro: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    id_invernadero: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    id_usuario: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    zona: Mapped[str] = mapped_column(String(50), nullable=False)
    seccion: Mapped[str] = mapped_column(String(50), nullable=False)
    temperatura: Mapped[float] = mapped_column(Float, nullable=True)
    humedad: Mapped[float] = mapped_column(Float, nullable=True)
    tipo_observacion: Mapped[str] = mapped_column(String(50), nullable=False)
    especie_tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    notas: Mapped[str] = mapped_column(String(255), nullable=True) # Puede estar vacío
    nivel_infestacion: Mapped[str] = mapped_column(String(50), nullable=False)
    # Esto le dice a SQLAlchemy que un reporte puede tener muchos "observables"
    observables = relationship("ReporteObservable", back_populates="reporte")
    evidencias = relationship("EvidenciaMonitoreo", back_populates="reporte", cascade="all, delete-orphan")

# TABLA PARA EL ARREGLO DINÁMICO
class ReporteObservable(Base):
    __tablename__ = "reportes_observables"

    id_observable: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Llave foránea que lo amarra al reporte principal
    id_reporte: Mapped[int] = mapped_column(Integer, ForeignKey("reportes_monitoreo.id_reporte"), nullable=False) 
    
    punto_visible: Mapped[str] = mapped_column(String(100), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relación de vuelta hacia el reporte
    reporte = relationship("ReporteMonitoreo", back_populates="observables")

class EvidenciaMonitoreo(Base):
    __tablename__ = "evidencias_monitoreo"

    id_evidencia: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    id_reporte: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reportes_monitoreo.id_reporte"),
        nullable=False
    )

    url_foto: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    reporte = relationship(
        "ReporteMonitoreo",
        back_populates="evidencias"
    )

class CatalogoObservable(Base):
    __tablename__ = "catalogo_observables"

    id_observable = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)

class ZonaInvernadero(Base):
    __tablename__ = "zonas_invernadero"

    id_zona = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_invernadero = Column(
        Integer,
        ForeignKey("invernaderos.id", ondelete="CASCADE"),
        nullable=False
    )

    nombre = Column(
        String(100),
        nullable=False
    )

    estado = Column(
        String(30),
        nullable=False,
        default="Activo"
    )