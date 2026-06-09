# routes/ventas.py
# Registro de ventas y descuento de stock.

from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, request, session, url_for

from models.database import get_db
from utils.clientes import CLIENTE_ANONIMO_ID, asegurar_cliente_anonimo
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

    conn = get_db()

    if not cliente_id:
        asegurar_cliente_anonimo(conn)
        cliente_id = CLIENTE_ANONIMO_ID

    juego = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()
    cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()

    if not juego or not cliente:
        flash("Juego o cliente no valido.", "error")
        conn.close()
        return redirect(url_for("juegos.catalogo"))

    if juego["stock"] < cantidad:
        flash(f"Stock insuficiente. Disponible: {juego['stock']}", "error")
        conn.close()
        return redirect(url_for("juegos.detalle", juego_id=juego_id))

    total = juego["precio"] * cantidad
    fecha_colombia = (datetime.utcnow() - OFFSET_COLOMBIA).strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        """
        INSERT INTO ventas
            (cliente_id, cliente_nombre, juego_id, juego_nombre,
             cantidad, precio_unitario, total, vendedor, fecha)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            cliente["id"],
            cliente["nombre"],
            juego["id"],
            juego["title"],
            cantidad,
            juego["precio"],
            total,
            session["empleado_nombre"],
            fecha_colombia,
        ),
    )
    conn.execute("UPDATE juegos SET stock = stock - ? WHERE id = ?", (cantidad, juego_id))
    conn.commit()
    conn.close()

    etiqueta = "anonimo" if cliente_id == CLIENTE_ANONIMO_ID else cliente["nombre"]
    flash(f"Venta registrada - {etiqueta} - Total: ${total:,.2f}", "success")
    return redirect(url_for("juegos.detalle", juego_id=juego_id))
