from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.negocio import Negocio

ROLES = ("dueno", "cajero")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (CheckConstraint(f"rol IN {ROLES}", name="rol_valido"),)

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    id_negocio: Mapped[int] = mapped_column(ForeignKey("negocios.id_negocio"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)  # siempre en minúsculas
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(server_default=true())
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    negocio: Mapped[Negocio] = relationship()
