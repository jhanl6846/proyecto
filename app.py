# app.py
# Punto de entrada de la aplicacion Flask.

import os

import requests
from flasgger import Swagger
from flask import Flask

from models.database import DB_PATH, cargar_juegos_api, init_db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.juegos import juegos_bp
from routes.vendedor import vendedor_bp
from routes.ventas import ventas_bp

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs",
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Tienda de Juegos API",
        "description": (
            "Documentacion automatica de las rutas del sistema. "
            "Incluye autenticacion por rol, menu lateral, catalogo, inventario, "
            "ventas, cliente anonimo C000 y base de datos SQLite."
        ),
        "version": "2.1.0",
    },
    "host": "localhost:3000",
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/x-www-form-urlencoded"],
    "produces": ["text/html"],
}


def _cargar_juegos_desde_api(app: Flask) -> None:
    """Descarga el catalogo desde FreeToGame solo si la tabla esta vacia."""
    with app.app_context():
        print("Descargando juegos desde FreeToGame API...")
        try:
            resp = requests.get("https://www.freetogame.com/api/games", timeout=10)
            resp.raise_for_status()
            cargar_juegos_api(resp.json())
            print(f"{len(resp.json())} juegos disponibles para carga inicial.")
        except Exception as e:
            print(f"Error al cargar juegos: {e}")


def create_app() -> Flask:
    """Crear y configurar la instancia de Flask."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "clave-super-secreta-cambiar-en-prod")

    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(vendedor_bp, url_prefix="/vendedor")
    app.register_blueprint(juegos_bp, url_prefix="/juegos")
    app.register_blueprint(ventas_bp, url_prefix="/ventas")

    with app.app_context():
        init_db()
        print(f"Base de datos activa: {DB_PATH}")

    return app


app = create_app()

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        _cargar_juegos_desde_api(app)
    app.run(debug=True, port=3000)
else:
    _cargar_juegos_desde_api(app)
