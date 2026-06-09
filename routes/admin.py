# routes/admin.py
# Rutas exclusivas del panel de administrador

import random
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.database import get_db
from models.entidades import hashear_contrasena
from utils.clientes import contar_clientes_registrados, listar_clientes_registrados, siguiente_cliente_id
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
    conn = get_db()
    stats = {
        "total_juegos":    conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0],
        "total_empleados": conn.execute("SELECT COUNT(*) FROM empleados").fetchone()[0],
        "total_clientes":  contar_clientes_registrados(conn),
        "total_ventas":    conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0],
        "ingresos":        conn.execute("SELECT SUM(total) FROM ventas").fetchone()[0] or 0,
    }
    conn.close()
    return render_template("admin/dashboard.html", **stats)


# ──── Empleados ─────────────────────────────────────────────────────────────

@admin_bp.route("/empleados")
@requiere_admin
def lista_empleados():
    conn = get_db()
    empleados = conn.execute("SELECT * FROM empleados").fetchall()
    conn.close()
    return render_template("admin/empleados.html", empleados=empleados)


@admin_bp.route("/empleados/nuevo", methods=["GET", "POST"])
@requiere_admin
def nuevo_empleado():
    if request.method == "POST":
        conn = get_db()
        try:
            cedula_str = request.form.get("cedula", "").strip()
            if not cedula_str:
                flash("La cédula es obligatoria.", "error")
                return render_template("admin/nuevo_empleado.html")

            cedula = int(cedula_str)
            if conn.execute("SELECT id FROM empleados WHERE cedula = ?", (cedula,)).fetchone():
                flash(f"Ya existe un empleado con la cédula {cedula}.", "error")
                return render_template("admin/nuevo_empleado.html")

            max_id = conn.execute("SELECT MAX(id) FROM empleados").fetchone()[0]
            siguiente = int(max_id[1:]) + 1 if max_id else 1
            nuevo_id = f"E{siguiente:03}"

            direccion = request.form.get("direccion", "").strip() or \
                f"calle {random.randint(1, 100)} # {random.randint(1, 100)}-{random.randint(1, 100)}"
            telefono = request.form.get("telefono", "").strip() or \
                str(random.randint(3_000_000_000, 3_999_999_999))

            conn.execute(
                """
                INSERT INTO empleados (id, rango, contrasena, nombre, edad, cedula, direccion, telefono)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    nuevo_id,
                    request.form["rango"],
                    hashear_contrasena(request.form["contrasena"]),
                    request.form["nombre"].lower(),
                    int(request.form["edad"]),
                    cedula,
                    direccion,
                    telefono,
                ),
            )
            conn.commit()
            flash(f"Empleado {nuevo_id} registrado con éxito.", "success")
        except Exception as e:
            flash(f"Error al registrar: {e}", "error")
        finally:
            conn.close()
        return redirect(url_for("admin.lista_empleados"))

    return render_template("admin/nuevo_empleado.html")


@admin_bp.route("/empleados/eliminar/<emp_id>", methods=["POST"])
@requiere_admin
def eliminar_empleado(emp_id):
    conn = get_db()
    try:
        emp = conn.execute("SELECT * FROM empleados WHERE id = ?", (emp_id,)).fetchone()
        if not emp:
            flash("Empleado no encontrado.", "error")
        elif emp["rango"] == "administrador":
            total_admins = conn.execute(
                "SELECT COUNT(*) FROM empleados WHERE rango = 'administrador'"
            ).fetchone()[0]
            if total_admins <= 1:
                flash("No se puede eliminar el único administrador del sistema.", "error")
            else:
                conn.execute("DELETE FROM empleados WHERE id = ?", (emp_id,))
                conn.commit()
                flash(f"Empleado {emp_id} eliminado correctamente.", "success")
        else:
            conn.execute("DELETE FROM empleados WHERE id = ?", (emp_id,))
            conn.commit()
            flash(f"Empleado {emp_id} eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("admin.lista_empleados"))


# ──── Clientes ──────────────────────────────────────────────────────────────

@admin_bp.route("/clientes")
@requiere_admin
def lista_clientes():
    conn = get_db()
    clientes = listar_clientes_registrados(conn)
    conn.close()
    return render_template("admin/clientes.html", clientes=clientes)


@admin_bp.route("/clientes/nuevo", methods=["GET", "POST"])
@requiere_admin
def nuevo_cliente():
    next_url = request.values.get("next") or url_for("admin.lista_clientes")
    if not next_url.startswith("/"):
        next_url = url_for("admin.lista_clientes")

    if request.method == "POST":
        conn = get_db()
        nuevo_id = siguiente_cliente_id(conn)
        try:
            conn.execute(
                """
                INSERT INTO clientes (id, nombre, edad, cedula, direccion, telefono)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    nuevo_id,
                    request.form["nombre"].lower(),
                    int(request.form["edad"]),
                    int(request.form["cedula"]),
                    request.form.get("direccion") or
                        f"carrera {random.randint(1, 100)} # {random.randint(1, 100)}-{random.randint(1, 100)}",
                    request.form.get("telefono") or
                        str(random.randint(3_000_000_000, 3_999_999_999)),
                ),
            )
            conn.commit()
            flash(f"Cliente {nuevo_id} registrado con éxito.", "success")
        except Exception as e:
            flash(f"Error al registrar: {e}", "error")
        finally:
            conn.close()
        return redirect(next_url)

    return render_template("admin/nuevo_cliente.html", next_url=next_url)


@admin_bp.route("/clientes/eliminar/<cli_id>", methods=["POST"])
@requiere_admin
def eliminar_cliente(cli_id):
    conn = get_db()
    try:
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (cli_id,)).fetchone()
        if not cliente:
            flash("Cliente no encontrado.", "error")
        else:
            conn.execute("DELETE FROM clientes WHERE id = ?", (cli_id,))
            conn.commit()
            flash(f"Cliente {cli_id} eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("admin.lista_clientes"))


# ──── Ventas ────────────────────────────────────────────────────────────────

@admin_bp.route("/ventas")
@requiere_admin
def registro_ventas():
    conn = get_db()
    ventas = conn.execute("SELECT * FROM ventas ORDER BY fecha DESC").fetchall()
    conn.close()
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
