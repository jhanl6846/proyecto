# routes/ventas.py
# Registro de ventas y descuento de stock.

from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, request, session, url_for

from models.entidades import Venta
from utils.decorators import requiere_login

ventas_bp = Blueprint("ventas", __name__)

OFFSET_COLOMBIA = timedelta(hours=5)


@ventas_bp.route("/nueva", methods=["POST"])
@requiere_login
def nueva_venta():
    """
    Registrar una venta y descontar stock.
    ---
    tags:
      - Ventas
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: juego_id
        in: formData
        type: integer
        required: true
        description: ID del juego vendido.
      - name: cliente_id
        in: formData
        type: string
        required: false
        description: ID del cliente; si se omite se usa el cliente anonimo C000.
      - name: cantidad
        in: formData
        type: integer
        required: false
        description: Cantidad vendida.
    responses:
      302:
        description: Redireccion al detalle del juego o al catalogo si hay error.
    """
    juego_id = int(request.form["juego_id"])
    cliente_id = request.form.get("cliente_id", "").strip()
    cantidad = int(request.form.get("cantidad", 1))
    fecha_colombia = (datetime.utcnow() - OFFSET_COLOMBIA).strftime("%Y-%m-%d %H:%M:%S")

    resultado = Venta.registrar(
        juego_id=juego_id,
        cliente_id=cliente_id,
        cantidad=cantidad,
        vendedor=session["empleado_nombre"],
        fecha=fecha_colombia,
    )

    if not resultado["ok"]:
        flash(resultado["error"], "error")
        if resultado["juego_id"]:
            return redirect(url_for("juegos.detalle", juego_id=resultado["juego_id"]))
        return redirect(url_for("juegos.catalogo"))

    flash(
        f"Venta registrada - {resultado['etiqueta']} - Total: ${resultado['total']:,.2f}",
        "success",
    )
    return redirect(url_for("juegos.detalle", juego_id=juego_id))
