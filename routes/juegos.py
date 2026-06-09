# routes/juegos.py
# Rutas del catálogo de juegos, inventario, descuentos y mejores calificados

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import get_db
from models.entidades import Juego, Cliente
from utils.clientes import listar_clientes_registrados
from utils.decorators import requiere_login

juegos_bp = Blueprint("juegos", __name__)


@juegos_bp.route("/")
@requiere_login
def catalogo():
    conn = get_db()
    q          = request.args.get("q", "").lower()
    genero     = request.args.get("genero", "")
    plataforma = request.args.get("plataforma", "")
    editorial  = request.args.get("editorial", "")

    query  = "SELECT * FROM juegos WHERE 1=1"
    params = []
    if q:
        query += " AND title LIKE ?"
        params.append(f"%{q}%")
    if genero:
        query += " AND genre = ?"
        params.append(genero)
    if plataforma:
        query += " AND platform = ?"
        params.append(plataforma)
    if editorial:
        query += " AND publisher = ?"
        params.append(editorial)
    query += " LIMIT 60"

    filas_juegos = conn.execute(query, params).fetchall()
    juegos = [Juego.desde_fila_db(f) for f in filas_juegos]

    generos     = [r[0] for r in conn.execute("SELECT DISTINCT genre FROM juegos ORDER BY genre").fetchall()]
    plataformas = [r[0] for r in conn.execute("SELECT DISTINCT platform FROM juegos ORDER BY platform").fetchall()]
    editoriales = [r[0] for r in conn.execute("SELECT DISTINCT publisher FROM juegos ORDER BY publisher").fetchall()]
    conn.close()

    return render_template(
        "juegos/catalogo.html",
        juegos=juegos,
        generos=generos,
        plataformas=plataformas,
        editoriales=editoriales,
        q=q, genero=genero, plataforma=plataforma, editorial=editorial,
    )


@juegos_bp.route("/<int:juego_id>")
@requiere_login
def detalle(juego_id):
    conn = get_db()
    fila_juego     = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()
    # Excluir cliente anónimo C000 de la lista de selección
    filas_clientes = listar_clientes_registrados(conn)
    conn.close()

    if not fila_juego:
        flash("Juego no encontrado.", "error")
        return redirect(url_for("juegos.catalogo"))

    juego    = Juego.desde_fila_db(fila_juego)
    clientes = [Cliente.desde_fila_db(f) for f in filas_clientes]
    es_admin = session.get("empleado_rango") == "administrador"
    return render_template("juegos/detalle.html", juego=juego, clientes=clientes, es_admin=es_admin)


@juegos_bp.route("/<int:juego_id>/descuento", methods=["POST"])
@requiere_login
def aplicar_descuento(juego_id):
    # Solo admins pueden aplicar descuentos
    if session.get("empleado_rango") != "administrador":
        flash("Solo el administrador puede aplicar descuentos.", "error")
        return redirect(url_for("juegos.detalle", juego_id=juego_id))

    porcentaje = int(request.form.get("porcentaje", 0))
    conn = get_db()
    fila = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()

    if fila and 0 < porcentaje < 100:
        juego = Juego.desde_fila_db(fila)
        nuevo_precio = round(juego.precio * (1 - porcentaje / 100), 2)
        conn.execute("UPDATE juegos SET precio = ? WHERE id = ?", (nuevo_precio, juego_id))
        conn.commit()
        flash(f"Descuento del {porcentaje}% aplicado. Nuevo precio: ${nuevo_precio:,.2f}", "success")

    conn.close()
    return redirect(url_for("juegos.detalle", juego_id=juego_id))


@juegos_bp.route("/mejores")
@requiere_login
def mejor_calificados():
    conn = get_db()
    filas = conn.execute("SELECT * FROM juegos ORDER BY calificacion DESC LIMIT 20").fetchall()
    conn.close()
    juegos = [Juego.desde_fila_db(f) for f in filas]
    return render_template("juegos/mejores.html", juegos=juegos)


@juegos_bp.route("/inventario")
@requiere_login
def valor_inventario():
    conn = get_db()
    filas    = conn.execute("SELECT * FROM juegos WHERE stock > 0 ORDER BY precio DESC LIMIT 20").fetchall()
    total    = conn.execute("SELECT SUM(precio * stock) FROM juegos").fetchone()[0] or 0
    cantidad = conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0]
    conn.close()
    juegos = [Juego.desde_fila_db(f) for f in filas]
    return render_template("juegos/inventario.html", juegos=juegos, total=total, cantidad=cantidad)
