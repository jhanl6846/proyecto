# app.py
# Punto de entrada de la aplicación Flask

import os
import requests
from flask import Flask
from flasgger import Swagger

from models.database import DB_PATH, init_db, cargar_juegos_api
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.vendedor import vendedor_bp
from routes.juegos import juegos_bp
from routes.ventas import ventas_bp

# ── Configuración de Swagger ────────────────────────────────────────────────
#
# La documentación se genera AUTOMÁTICAMENTE a partir de los docstrings
# de cada función de vista, usando el formato de flasgger.
# No es necesario editar ningun archivo YAML externo: cada vez que agregues
# o modifiques una ruta, solo actualiza su docstring y Swagger se actualiza.
#
# La UI estará disponible en: http://localhost:3000/apidocs
#
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,   # incluir todas las rutas
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
            "Documentación automática de las rutas del sistema. "
            "Se actualiza sola al modificar los docstrings de cada vista."
        ),
        "version": "2.0.0",
    },
    "host": "localhost:3000",
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/x-www-form-urlencoded"],
    "produces": ["text/html"],
}


def _cargar_juegos_desde_api(app: Flask) -> None:
    """Descarga el catálogo desde FreeToGame solo si la tabla está vacía."""
    with app.app_context():
        print("Descargando juegos desde FreeToGame API...")
        try:
            resp = requests.get("https://www.freetogame.com/api/games", timeout=10)
            resp.raise_for_status()
            cargar_juegos_api(resp.json())
            print(f"{len(resp.json())} juegos cargados exitosamente.")
        except Exception as e:
            print(f"Error al cargar juegos: {e}")


def create_app() -> Flask:
    """Crear y configurar la instancia de Flask."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "clave-super-secreta-cambiar-en-prod")

    # Swagger generado desde docstrings (sin archivo YAML externo)
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp,    url_prefix="/admin")
    app.register_blueprint(vendedor_bp, url_prefix="/vendedor")
    app.register_blueprint(juegos_bp,   url_prefix="/juegos")
    app.register_blueprint(ventas_bp,   url_prefix="/ventas")

    # Base de datos
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




#           como crear el entorno virtual
# python -m venv proyecto
#      activar entorno virtual
# \proyecto\Scripts\Activate
#      desactivar entorno virtual
# deactivate
#        comandos para guarad cambios al githud
# git status
# git add .
# git commit -m "Actualizar "
# git push origin main

#        como instalar dependencias
# pip install -r requirements.txt  
#        como crear el archivo requirements.txt
# pip freeze > requirements.txt

 #pip install Flask flasgger requests
#  cd proyecto-_programacion
# git pull origin main