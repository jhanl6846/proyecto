# routes/admin.py
# Rutas exclusivas del panel de administrador

import random
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.database import get_db
from models.entidades import Cliente, Empleado, Juego, Venta
from utils.clientes import (
    buscar_cliente_por_cedula,
    buscar_empleado_por_cedula,
    datos_cliente_desde_empleado,
)
from utils.decorators import requiere_admin

admin_bp = Blueprint("admin", __name__)

CAMPO_DESCUENTO = {
    "genero": "genre",
    "plataforma": "platform",
    "editorial": "publisher",
}

@admin_bp.route("/")
@requiere_admin
def dashboard():
    stats = {
        "total_juegos":    Juego.contar(),
        "total_empleados": Empleado.contar(),
        "total_clientes":  Cliente.contar_registrados(),
        "total_ventas":    Venta.contar(),
        "ingresos":        Venta.ingresos_totales(),
    }
    return render_template("admin/dashboard.html", **stats)


# ──── Empleados ─────────────────────────────────────────────────────────────

@admin_bp.route("/empleados")
@requiere_admin
def lista_empleados():
    empleados = Empleado.listar_todos()
    return render_template("admin/empleados.html", empleados=empleados)


@admin_bp.route("/empleados/nuevo", methods=["GET", "POST"])
@requiere_admin
def nuevo_empleado():
    if request.method == "POST":
        try:
            cedula_str = request.form.get("cedula", "").strip()
            if not cedula_str:
                flash("La cédula es obligatoria.", "error")
                return render_template("admin/nuevo_empleado.html")

            cedula = int(cedula_str)
            if Empleado.buscar_por_cedula(cedula):
                flash(f"Ya existe un empleado con la cédula {cedula}.", "error")
                return render_template("admin/nuevo_empleado.html")

            direccion = request.form.get("direccion", "").strip() or \
                f"calle {random.randint(1, 100)} # {random.randint(1, 100)}-{random.randint(1, 100)}"
            telefono = request.form.get("telefono", "").strip() or \
                str(random.randint(3_000_000_000, 3_999_999_999))

            nuevo_id = Empleado.crear(
                nombre=request.form["nombre"],
                rango=request.form["rango"],
                contrasena=request.form["contrasena"],
                edad=request.form["edad"],
                cedula=cedula,
                direccion=direccion,
                telefono=telefono,
            )
            flash(f"Empleado {nuevo_id} registrado con éxito.", "success")
        except Exception as e:
            flash(f"Error al registrar: {e}", "error")
        return redirect(url_for("admin.lista_empleados"))

    return render_template("admin/nuevo_empleado.html")


@admin_bp.route("/empleados/eliminar/<emp_id>", methods=["POST"])
@requiere_admin
def eliminar_empleado(emp_id):
    try:
        emp = Empleado.buscar_por_id(emp_id)
        if not emp:
            flash("Empleado no encontrado.", "error")
        elif emp.rango == "administrador":
            total_admins = Empleado.contar_administradores()
            if total_admins <= 1:
                flash("No se puede eliminar el único administrador del sistema.", "error")
            else:
                Empleado.eliminar(emp_id)
                flash(f"Empleado {emp_id} eliminado correctamente.", "success")
        else:
            Empleado.eliminar(emp_id)
            flash(f"Empleado {emp_id} eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    return redirect(url_for("admin.lista_empleados"))


# ──── Clientes ──────────────────────────────────────────────────────────────

@admin_bp.route("/clientes")
@requiere_admin
def lista_clientes():
    clientes = Cliente.listar_registrados()
    return render_template("admin/clientes.html", clientes=clientes)


@admin_bp.route("/clientes/nuevo", methods=["GET", "POST"])
@requiere_admin
def nuevo_cliente():
    next_url = request.values.get("next") or url_for("admin.lista_clientes")
    if not next_url.startswith("/"):
        next_url = url_for("admin.lista_clientes")
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
                return redirect(url_for("admin.nuevo_cliente", cedula=cedula, next=next_url))

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
            flash(f"Error al registrar: {e}", "error")
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
        "admin/nuevo_cliente.html",
        cliente_existente=cliente_existente,
        datos_cliente=datos_cliente,
        empleado_encontrado=empleado_encontrado,
        next_url=next_url,
    )


@admin_bp.route("/clientes/eliminar/<cli_id>", methods=["POST"])
@requiere_admin
def eliminar_cliente(cli_id):
    try:
        cliente = Cliente.buscar_por_id(cli_id)
        if not cliente:
            flash("Cliente no encontrado.", "error")
        else:
            Cliente.eliminar(cli_id)
            flash(f"Cliente {cli_id} eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    return redirect(url_for("admin.lista_clientes"))


# ──── Ventas ────────────────────────────────────────────────────────────────

@admin_bp.route("/ventas")
@requiere_admin
def registro_ventas():
    ventas = Venta.listar_todas()
    return render_template("admin/ventas.html", ventas=ventas)


# ──── Juegos (solo admin) ────────────────────────────────────────────────────

@admin_bp.route("/juegos/nuevo", methods=["GET", "POST"])
@requiere_admin
def nuevo_juego():
    if request.method == "POST":
        conn = get_db()
        try:
            titulo = request.form.get("title", "").strip()
            if not titulo:
                flash("El título del juego es obligatorio.", "error")
                return render_template("admin/nuevo_juego.html")

            precio = float(request.form.get("precio", 0))
            stock = int(request.form.get("stock", 0))
            calificacion = float(request.form.get("calificacion", 5.0))

            conn.execute(
                """
                INSERT INTO juegos
                (title, thumbnail, short_description, game_url, genre, platform,
                 publisher, developer, release_date, freetogame_profile_url,
                 precio, calificacion, stock)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    titulo.lower(),
                    request.form.get("thumbnail", "").strip(),
                    request.form.get("short_description", "").strip().lower(),
                    request.form.get("game_url", "").strip(),
                    request.form.get("genre", "").strip().lower(),
                    request.form.get("platform", "").strip().lower(),
                    request.form.get("publisher", "").strip().lower(),
                    request.form.get("developer", "").strip().lower(),
                    request.form.get("release_date", "").strip(),
                    "",
                    precio,
                    calificacion,
                    stock,
                ),
            )
            conn.commit()
            flash(f"Juego '{titulo}' agregado al catálogo con éxito.", "success")
        except Exception as e:
            flash(f"Error al agregar juego: {e}", "error")
        finally:
            conn.close()
        return redirect(url_for("juegos.catalogo"))

    return render_template("admin/nuevo_juego.html")


@admin_bp.route("/juegos/eliminar/<int:juego_id>", methods=["POST"])
@requiere_admin
def eliminar_juego(juego_id):
    conn = get_db()
    try:
        juego = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()
        if not juego:
            flash("Juego no encontrado.", "error")
        else:
            conn.execute("DELETE FROM juegos WHERE id = ?", (juego_id,))
            conn.commit()
            flash(f"Juego '{juego['title']}' eliminado del catálogo.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("juegos.catalogo"))


# ──── Descuentos masivos ─────────────────────────────────────────────────────

@admin_bp.route("/descuentos", methods=["GET", "POST"])
@requiere_admin
def descuentos():
    conn = get_db()
    generos     = [r[0] for r in conn.execute("SELECT DISTINCT genre    FROM juegos").fetchall()]
    plataformas = [r[0] for r in conn.execute("SELECT DISTINCT platform FROM juegos").fetchall()]
    editoriales = [r[0] for r in conn.execute("SELECT DISTINCT publisher FROM juegos").fetchall()]
    conn.close()

    if request.method == "POST":
        tipo       = request.form["tipo"]
        valor      = request.form["valor"]
        porcentaje = int(request.form["porcentaje"])
        campo      = CAMPO_DESCUENTO.get(tipo)

        if campo:
            conn = get_db()
            juegos = conn.execute(f"SELECT * FROM juegos WHERE {campo} = ?", (valor,)).fetchall()
            for j in juegos:
                nuevo_precio = round(j["precio"] * (1 - porcentaje / 100), 2)
                conn.execute("UPDATE juegos SET precio = ? WHERE id = ?", (nuevo_precio, j["id"]))
            conn.commit()
            conn.close()
            flash(f"Descuento del {porcentaje}% aplicado a {len(juegos)} juegos de «{valor}».", "success")

        return redirect(url_for("admin.descuentos"))

    return render_template(
        "admin/descuentos.html",
        generos=generos,
        plataformas=plataformas,
        editoriales=editoriales,
    )
