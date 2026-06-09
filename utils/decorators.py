# utils/decorators.py
# Decoradores reutilizables para proteger rutas

from functools import wraps
from flask import session, redirect, url_for, flash
def requiere_login(f):
    """Redirige al login si el empleado no tiene sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "empleado_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated
def requiere_admin(f):
    """Permite el acceso solo a empleados con rango administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("empleado_rango") != "administrador":
            flash("Acceso restringido a administradores.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated
