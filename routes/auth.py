# routes/auth.py
# Rutas de autenticación: login y logout

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.entidades import Empleado

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    """
    Mostrar formulario de inicio de sesión o procesar credenciales.
    ---
    tags:
      - Autenticacion
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: id
        in: formData
        type: string
        required: true
        description: ID del empleado (ej. E001)
        example: E001
      - name: contrasena
        in: formData
        type: string
        required: true
        description: Contraseña del empleado
        example: "123456"
    responses:
      200:
        description: Página HTML de login (GET o error de credenciales).
      302:
        description: Redirección al panel correspondiente según el rango.
    """
    if request.method == "POST":
        emp_id = request.form.get("id", "").upper()
        contrasena = request.form.get("contrasena", "")

        empleado = Empleado.buscar_por_id(emp_id)

        if not empleado:
            flash("ID de empleado no encontrado.", "error")
            return render_template("login.html")

        if not empleado.verificar_contrasena(contrasena):
            flash("Contraseña incorrecta.", "error")
            return render_template("login.html")

        session["empleado_id"] = empleado.id
        session["empleado_nombre"] = empleado.nombre
        session["empleado_rango"] = empleado.rango

        if empleado.rango == "administrador":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("vendedor.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """
    Cerrar sesión del empleado actual.
    ---
    tags:
      - Autenticacion
    responses:
      302:
        description: Redirección a la página de login.
    """
    session.clear()
    return redirect(url_for("auth.login"))
