from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

METODOS_ABONO = ("efectivo", "tarjeta", "transferencia")


class Deuda(Base):
    """Nace de una venta al fiao. El estado (pendiente/parcial/pagada/vencida) se calcula
    con saldo_pendiente y fecha_limite; no se guarda para que no se desincronice."""

    __tablename__ = "deudas"
    __table_args__ = (
        CheckConstraint(
            "saldo_pendiente >= 0 AND saldo_pendiente <= monto_total", name="saldo_valido"
        ),
    )

    id_deuda: Mapped[int] = mapped_column(primary_key=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id_cliente"), index=True)
    id_venta: Mapped[int] = mapped_column(ForeignKey("ventas.id_venta"), unique=True)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    saldo_pendiente: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fecha_limite: Mapped[date | None]
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())


class Abono(Base):
    __tablename__ = "abonos"
    __table_args__ = (
        CheckConstraint("monto > 0", name="monto_positivo"),
        CheckConstraint(f"metodo_pago IN {METODOS_ABONO}", name="metodo_pago_valido"),
    )

    id_abono: Mapped[int] = mapped_column(primary_key=True)
    id_deuda: Mapped[int] = mapped_column(ForeignKey("deudas.id_deuda"), index=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    metodo_pago: Mapped[str] = mapped_column(String(15))
    nota: Mapped[str | None] = mapped_column(String(255))
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())


class RecordatorioWhatsapp(Base):
    """Cada aviso enviado queda aquí: evita duplicados y deja traza."""

    __tablename__ = "recordatorios_whatsapp"
    __table_args__ = (CheckConstraint("estado IN ('enviado', 'fallido')", name="estado_valido"),)

    id_recordatorio: Mapped[int] = mapped_column(primary_key=True)
    id_deuda: Mapped[int] = mapped_column(ForeignKey("deudas.id_deuda"), index=True)
    enviado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    estado: Mapped[str] = mapped_column(String(10))
    id_mensaje_meta: Mapped[str | None] = mapped_column(String(100))
    error: Mapped[str | None] = mapped_column(Text)
