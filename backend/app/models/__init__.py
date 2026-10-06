# Alembic descubre las tablas importando este paquete: todo modelo nuevo se importa aquí.
from app.models.cliente import Cliente
from app.models.fiao import Abono, Deuda, RecordatorioWhatsapp
from app.models.inventario import Categoria, Producto
from app.models.negocio import Negocio
from app.models.usuario import Usuario
from app.models.venta import DetalleVenta, Venta

__all__ = [
    "Abono",
    "Categoria",
    "Cliente",
    "DetalleVenta",
    "Deuda",
    "Negocio",
    "Producto",
    "RecordatorioWhatsapp",
    "Usuario",
    "Venta",
]
