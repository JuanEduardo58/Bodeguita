from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Negocio(Base):
    """Un colmado. Todo lo demás cuelga de aquí (SaaS: varios colmados por instalación)."""

    __tablename__ = "negocios"

    id_negocio: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(20))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
