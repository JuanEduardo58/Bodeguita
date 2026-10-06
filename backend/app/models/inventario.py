from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

UNIDADES = ("unidad", "libra", "onza", "litro")


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("id_negocio", "nombre"),)

    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    id_negocio: Mapped[int] = mapped_column(ForeignKey("negocios.id_negocio"), index=True)
    nombre: Mapped[str] = mapped_column(String(80))
    activo: Mapped[bool] = mapped_column(server_default=true())


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint("id_negocio", "codigo_barras"),
        CheckConstraint(f"unidad_medida IN {UNIDADES}", name="unidad_valida"),
        CheckConstraint("precio_venta >= 0 AND precio_costo >= 0", name="precios_positivos"),
    )

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    id_negocio: Mapped[int] = mapped_column(ForeignKey("negocios.id_negocio"), index=True)
    id_categoria: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id_categoria"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(50))
    # Cantidades decimales: en el colmado se vende media libra de arroz.
    unidad_medida: Mapped[str] = mapped_column(String(10), server_default="unidad")
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio_costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), server_default="0")
    stock_actual: Mapped[Decimal] = mapped_column(Numeric(10, 3), server_default="0")
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(10, 3), server_default="0")
    activo: Mapped[bool] = mapped_column(server_default=true())
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
