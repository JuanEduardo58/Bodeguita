from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

METODOS_PAGO = ("efectivo", "tarjeta", "transferencia", "fiao")
ESTADOS_VENTA = ("completada", "anulada")


class Venta(Base):
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint(f"metodo_pago IN {METODOS_PAGO}", name="metodo_pago_valido"),
        CheckConstraint(f"estado IN {ESTADOS_VENTA}", name="estado_valido"),
        CheckConstraint("total >= 0", name="total_positivo"),
        CheckConstraint(
            "metodo_pago <> 'fiao' OR id_cliente IS NOT NULL", name="fiao_requiere_cliente"
        ),
    )

    id_venta: Mapped[int] = mapped_column(primary_key=True)
    id_negocio: Mapped[int] = mapped_column(ForeignKey("negocios.id_negocio"), index=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), index=True)
    id_cliente: Mapped[int | None] = mapped_column(ForeignKey("clientes.id_cliente"), index=True)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    metodo_pago: Mapped[str] = mapped_column(String(15))
    estado: Mapped[str] = mapped_column(String(15), server_default="completada")


class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    __table_args__ = (CheckConstraint("cantidad > 0", name="cantidad_positiva"),)

    id_detalle: Mapped[int] = mapped_column(primary_key=True)
    id_venta: Mapped[int] = mapped_column(ForeignKey("ventas.id_venta"), index=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("productos.id_producto"), index=True)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # congelado al vender
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
