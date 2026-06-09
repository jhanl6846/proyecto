CLIENTE_ANONIMO_ID = "C000"
CLIENTE_ANONIMO_NOMBRE = "cliente anonimo"


def contar_clientes_registrados(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM clientes WHERE id != ?",
        (CLIENTE_ANONIMO_ID,),
    ).fetchone()[0]


def listar_clientes_registrados(conn):
    return conn.execute(
        "SELECT * FROM clientes WHERE id != ? ORDER BY nombre",
        (CLIENTE_ANONIMO_ID,),
    ).fetchall()


def siguiente_cliente_id(conn):
    max_id = conn.execute(
        "SELECT MAX(CAST(SUBSTR(id, 2) AS INTEGER)) FROM clientes WHERE id != ?",
        (CLIENTE_ANONIMO_ID,),
    ).fetchone()[0]
    return f"C{(max_id or 0) + 1:03}"


def asegurar_cliente_anonimo(conn):
    existe = conn.execute(
        "SELECT id FROM clientes WHERE id = ?",
        (CLIENTE_ANONIMO_ID,),
    ).fetchone()
    if existe:
        return

    conn.execute(
        """
        INSERT OR IGNORE INTO clientes
            (id, nombre, edad, cedula, direccion, telefono)
        VALUES (?,?,?,?,?,?)
        """,
        (CLIENTE_ANONIMO_ID, CLIENTE_ANONIMO_NOMBRE, 0, 0, "-", "-"),
    )
    conn.commit()
