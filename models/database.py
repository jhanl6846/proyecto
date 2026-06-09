import sqlite3
import os
import random
from models.entidades import hashear_contrasena
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.abspath(os.environ.get("TIENDA_DB_PATH", os.path.join(BASE_DIR, "tienda.db")))
def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def _schema_exists(conn):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'empleados'"
    ).fetchone() is not None
def get_db():
    conn = _connect()
    if not _schema_exists(conn):
        conn.close()
        init_db()
        conn = _connect()
    return conn
def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id TEXT PRIMARY KEY,
            rango TEXT NOT NULL,
            contrasena TEXT NOT NULL,
            nombre TEXT NOT NULL,
            edad INTEGER,
            cedula INTEGER UNIQUE,
            direccion TEXT,
            telefono TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            edad INTEGER,
            cedula INTEGER UNIQUE,
            direccion TEXT,
            telefono TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS juegos (
            id INTEGER PRIMARY KEY,
            title TEXT,
            thumbnail TEXT,
            short_description TEXT,
            game_url TEXT,
            genre TEXT,
            platform TEXT,
            publisher TEXT,
            developer TEXT,
            release_date TEXT,
            freetogame_profile_url TEXT,
            precio REAL,
            calificacion REAL,
            stock INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id TEXT,
            cliente_nombre TEXT,
            juego_id INTEGER,
            juego_nombre TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            total REAL,
            vendedor TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Empleado admin por defecto si no existe
    admin = c.execute("SELECT * FROM empleados WHERE id='E001'").fetchone()
    if not admin:
        c.execute("""
            INSERT INTO empleados (id, rango, contrasena, nombre, edad, cedula, direccion, telefono)
            VALUES ('E001', 'administrador', ?, 'rodolfo', 45, 123456789, 'carrera 7# 14 - 36', '3158046788')
        """, (hashear_contrasena("123456"),))
    conn.commit()
    conn.close()
def cargar_juegos_api(juegos_json):
    """Carga los juegos desde la API si la tabla está vacía."""
    conn = get_db()
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM juegos").fetchone()[0]
    if count == 0:
        for x in juegos_json:
            c.execute("""
                INSERT OR IGNORE INTO juegos
                (id, title, thumbnail, short_description, game_url, genre, platform,
                 publisher, developer, release_date, freetogame_profile_url, precio, calificacion, stock)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                x["id"],
                x["title"].lower(),
                x["thumbnail"].lower(),
                x["short_description"].lower(),
                x["game_url"].lower(),
                x["genre"].lower().strip(),
                x["platform"].lower(),
                x["publisher"].lower(),
                x["developer"].lower(),
                x["release_date"].lower(),
                x["freetogame_profile_url"].lower(),
                random.randint(20000, 70000),
                round(random.uniform(1, 10), 1),
                random.randint(1, 10)
            ))
        conn.commit()
    conn.close()
