# routes/vendedor.py
# Rutas del panel del vendedor: dashboard y gestión de clientes

import random
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.database import get_db
from models.entidades import Cliente, Juego, Venta
from utils.clientes import (
    buscar_cliente_por_cedula,
    buscar_empleado_por_cedula,
    contar_clientes_registrados,
    datos_cliente_desde_empleado,
    listar_clientes_registrados,
    siguiente_cliente_id,
)
from utils.decorators import requiere_login

vendedor_bp = Blueprint("vendedor", __name__)


@vendedor_bp.route("/")
@requiere_login
def dashboard():
    """
    Mostrar el panel principal del vendedor con sus estadísticas.
    ---
    tags:
      - Vendedor
    responses:
      200:
        description: Página HTML del dashboard del vendedor con totales de juegos, clientes y sus ventas.
      302:
        description: Redirección al login si no hay sesión activa.
    """
    stats = {
        "total_juegos":   Juego.contar(),
        "total_clientes": Cliente.contar_registrados(),
        "mis_ventas":     Venta.contar_por_vendedor(session["empleado_nombre"]),
    }
    return render_template("vendedor/dashboard.html", **stats)


@vendedor_bp.route("/ventas")
@requiere_login
def mis_ventas():
    """
    Mostrar las ventas registradas por el vendedor actual.
    ---
    tags:
      - Vendedor
    responses:
      200:
        description: Pagina HTML con las ventas filtradas por el vendedor autenticado.
      302:
        description: Redireccion al login si no hay sesion activa.
    """
    ventas = Venta.listar_por_vendedor(session["empleado_nombre"])
    return render_template("admin/ventas.html", ventas=ventas)


@vendedor_bp.route("/clientes")
@requiere_login
def lista_clientes():
    """
    Listar todos los clientes registrados (vista vendedor).
    ---
    tags:
      - Vendedor
    responses:
      200:
        description: Página HTML con la lista de clientes.
      302:
        description: Redirección al login si no hay sesión activa.
    """
    clientes = Cliente.listar_registrados()
    return render_template("vendedor/clientes.html", clientes=clientes)


@vendedor_bp.route("/clientes/nuevo", methods=["GET", "POST"])
@requiere_login
def nuevo_cliente():
    """
    Mostrar formulario o registrar un nuevo cliente desde el panel vendedor.
    ---
    tags:
      - Vendedor
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: nombre
        in: formData
        type: string
        required: true
        description: Nombre completo del cliente.
      - name: edad
        in: formData
        type: integer
        required: true
        description: Edad del cliente.
      - name: cedula
        in: formData
        type: integer
        required: true
        description: Número de cédula (único).
      - name: direccion
        in: formData
        type: string
        required: false
        description: Dirección (se genera aleatoriamente si se omite).
      - name: telefono
        in: formData
        type: string
        required: false
        description: Teléfono (se genera aleatoriamente si se omite).
    responses:
      200:
        description: Página HTML del formulario de creación.
      302:
        description: Redirección a la lista de clientes tras crear correctamente.
    """
    next_url = request.values.get("next") or url_for("vendedor.lista_clientes")
    if not next_url.startswith("/"):
        next_url = url_for("vendedor.lista_clientes")
    cedula_consultada = request.values.get("cedula", "").strip()
    empleado_encontrado = None
    cliente_existente = None
    datos_cliente = None

    if request.method == "POST":
        conn = get_db()
        try:
            cedula = int(request.form["cedula"])
            cliente_existente = buscar_cliente_por_cedula(conn, cedula)
            if cliente_existente:
                flash(f"La cedula {cedula} ya esta registrada como cliente.", "error")
                return redirect(url_for("vendedor.nuevo_cliente", cedula=cedula, next=next_url))

            empleado_encontrado = buscar_empleado_por_cedula(conn, cedula)
            nombre = request.form.get("nombre", "").strip().lower()
            edad = request.form.get("edad", "").strip()
            direccion = request.form.get("direccion", "").strip()
            telefono = request.form.get("telefono", "").strip()
            nuevo_id = Cliente.crear(
                nombre=nombre,
                edad=edad,
                cedula=cedula,
                direccion=direccion or
                    f"carrera {random.randint(1, 100)} # {random.randint(1, 100)}-{random.randint(1, 100)}",
                telefono=telefono or str(random.randint(3_000_000_000, 3_999_999_999)),
            )
            flash(f"Cliente {nuevo_id} registrado con éxito.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        finally:
            conn.close()
        return redirect(next_url)

    if cedula_consultada:
        conn = get_db()
        try:
            cedula = int(cedula_consultada)
            cliente_existente = buscar_cliente_por_cedula(conn, cedula)
            empleado_encontrado = buscar_empleado_por_cedula(conn, cedula)
            datos_cliente = datos_cliente_desde_empleado(empleado_encontrado, cedula)
        except ValueError:
            flash("La cedula debe ser numerica.", "error")
        finally:
            conn.close()

    return render_template(
        "vendedor/nuevo_cliente.html",
        cliente_existente=cliente_existente,
        datos_cliente=datos_cliente,
        empleado_encontrado=empleado_encontrado,
        next_url=next_url,
    )
