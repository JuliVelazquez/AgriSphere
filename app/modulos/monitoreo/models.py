from sqlalchemy import Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.database import Base 

class ReporteMonitoreo(Base):
    __tablename__ = "reportes_monitoreo"

    id_reporte: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha_registro: Mapped[date] = mapped_column(Date, nullable=False)
    id_invernadero: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    id_usuario: Mapped[int] = mapped_column(Integer, index=True, nullable=False)