from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        CheckConstraint("limite_credito >= 0", name="limite_positivo"),
        # Meta exige consentimiento y un número válido para escribirle al cliente.
        CheckConstraint(
            "NOT acepta_whatsapp OR telefono IS NOT NULL", name="whatsapp_requiere_telefono"
        ),
    )

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    id_negocio: Mapped[int] = mapped_column(ForeignKey("negocios.id_negocio"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(20))  # formato E.164: +18095551234
    limite_credito: Mapped[Decimal] = mapped_column(Numeric(12, 2), server_default="0")
    acepta_whatsapp: Mapped[bool] = mapped_column(server_default=false())
    activo: Mapped[bool] = mapped_column(server_default=true())
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
