# models/entidades.py
from werkzeug.security import generate_password_hash, check_password_hash


def hashear_contrasena(contrasena_plana: str) -> str:
    """Genera un hash seguro (scrypt) de la contraseña en texto plano.
    Usar esta función antes de guardar cualquier contraseña en la BD."""
    return generate_password_hash(contrasena_plana)


class Empleado:
    """Superclase Base que mapea la tabla 'empleados'"""
    def __init__(self, id_emp, nombre, rango, contrasena, edad, cedula, direccion, telefono):
        self.id = id_emp
        self.nombre = nombre
        self.rango = rango
        self._contrasena_hash = contrasena  # Siempre es el hash almacenado en BD
        self.edad = edad
        self.cedula = cedula
        self.direccion = direccion
        self.telefono = telefono

    @classmethod
    def desde_fila_db(cls, fila):
        """Crea un objeto Empleado a partir de una fila de la base de datos."""
        if not fila:
            return None
        return cls(
            id_emp=fila["id"], nombre=fila["nombre"], rango=fila["rango"],
            contrasena=fila["contrasena"], edad=fila["edad"], cedula=fila["cedula"],
            direccion=fila["direccion"], telefono=fila["telefono"]
        )

    @classmethod
    def buscar_por_id(cls, emp_id):
        from models.database import get_db

        conn = get_db()
        fila = conn.execute("SELECT * FROM empleados WHERE id = ?", (emp_id,)).fetchone()
        conn.close()
        return cls.desde_fila_db(fila)

    @classmethod
    def buscar_por_cedula(cls, cedula):
        from models.database import get_db

        conn = get_db()
        fila = conn.execute("SELECT * FROM empleados WHERE cedula = ?", (cedula,)).fetchone()
        conn.close()
        return cls.desde_fila_db(fila)

    @classmethod
    def contar(cls):
        from models.database import get_db

        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM empleados").fetchone()[0]
        conn.close()
        return total

    @classmethod
    def listar_todos(cls):
        from models.database import get_db

        conn = get_db()
        filas = conn.execute("SELECT * FROM empleados").fetchall()
        conn.close()
        return filas

    @classmethod
    def contar_administradores(cls):
        from models.database import get_db

        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) FROM empleados WHERE rango = 'administrador'"
        ).fetchone()[0]
        conn.close()
        return total

    @classmethod
    def siguiente_id(cls):
        from models.database import get_db

        conn = get_db()
        max_id = conn.execute("SELECT MAX(id) FROM empleados").fetchone()[0]
        conn.close()
        siguiente = int(max_id[1:]) + 1 if max_id else 1
        return f"E{siguiente:03}"

    @classmethod
    def crear(cls, nombre, rango, contrasena, edad, cedula, direccion, telefono):
        from models.database import get_db

        nuevo_id = cls.siguiente_id()
        conn = get_db()
        conn.execute(
            """
            INSERT INTO empleados (id, rango, contrasena, nombre, edad, cedula, direccion, telefono)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                nuevo_id,
                rango,
                hashear_contrasena(contrasena),
                nombre.lower(),
                int(edad),
                int(cedula),
                direccion,
                telefono,
            ),
        )
        conn.commit()
        conn.close()
        return nuevo_id

    @classmethod
    def eliminar(cls, emp_id):
        from models.database import get_db

        conn = get_db()
        conn.execute("DELETE FROM empleados WHERE id = ?", (emp_id,))
        conn.commit()
        conn.close()

    def verificar_contrasena(self, contrasena_ingresada: str) -> bool:
        """Compara la contraseña ingresada contra el hash almacenado en BD."""
        return check_password_hash(self._contrasena_hash, contrasena_ingresada)

    def obtener_permisos(self):
        return ["ver_catalogo"]


# HERENCIA: Administrador y Vendedor heredan de Empleado
class Administrador(Empleado):
    def obtener_permisos(self):  # POLIMORFISMO
        return ["ver_catalogo", "gestionar_empleados", "aplicar_descuentos", "ver_ventas_globales"]

class Vendedor(Empleado):
    def obtener_permisos(self):  # POLIMORFISMO
        return ["ver_catalogo", "registrar_cliente", "registrar_venta"]


class Juego:
    """Clase que mapea la tabla 'juegos'"""
    def __init__(
        self,
        id_juego,
        title,
        precio,
        calificacion,
        stock,
        genre,
        platform,
        publisher,
        developer,
        release_date,
        short_description,
        thumbnail,
        game_url,
    ):
        self.id = id_juego
        self.title = title
        self.precio = precio
        self.calificacion = calificacion
        self.stock = stock
        self.genre = genre
        self.platform = platform
        self.publisher = publisher
        self.developer = developer
        self.release_date = release_date
        self.short_description = short_description
        self.thumbnail = thumbnail
        self.game_url = game_url

    @classmethod
    def desde_fila_db(cls, fila):
        if not fila:
            return None
        return cls(
            id_juego=fila["id"], title=fila["title"], precio=fila["precio"],
            calificacion=fila["calificacion"], stock=fila["stock"], genre=fila["genre"],
            platform=fila["platform"], publisher=fila["publisher"],
            developer=fila["developer"], release_date=fila["release_date"],
            short_description=fila["short_description"], thumbnail=fila["thumbnail"],
            game_url=fila["game_url"]
        )

    @classmethod
    def contar(cls):
        from models.database import get_db

        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM juegos").fetchone()[0]
        conn.close()
        return total

    @classmethod
    def buscar_por_id(cls, juego_id):
        from models.database import get_db

        conn = get_db()
        fila = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()
        conn.close()
        return cls.desde_fila_db(fila)

    @classmethod
    def eliminar(cls, juego_id):
        from models.database import get_db

        conn = get_db()
        conn.execute("DELETE FROM juegos WHERE id = ?", (juego_id,))
        conn.commit()
        conn.close()

    @classmethod
    def aplicar_descuento(cls, juego_id, porcentaje):
        from models.database import get_db

        juego = cls.buscar_por_id(juego_id)
        if not juego or not 0 < porcentaje < 100:
            return None

        nuevo_precio = round(juego.precio * (1 - porcentaje / 100), 2)
        conn = get_db()
        conn.execute("UPDATE juegos SET precio = ? WHERE id = ?", (nuevo_precio, juego_id))
        conn.commit()
        conn.close()
        return nuevo_precio

    @classmethod
    def crear(cls, datos):
        from models.database import get_db

        conn = get_db()
        conn.execute(
            """
            INSERT INTO juegos
            (title, thumbnail, short_description, game_url, genre, platform,
             publisher, developer, release_date, freetogame_profile_url,
             precio, calificacion, stock)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                datos["title"].lower(),
                datos.get("thumbnail", ""),
                datos.get("short_description", "").lower(),
                datos.get("game_url", ""),
                datos.get("genre", "").lower(),
                datos.get("platform", "").lower(),
                datos.get("publisher", "").lower(),
                datos.get("developer", "").lower(),
                datos.get("release_date", ""),
                datos.get("freetogame_profile_url", ""),
                float(datos["precio"]),
                float(datos["calificacion"]),
                int(datos["stock"]),
            ),
        )
        conn.commit()
        conn.close()

    def reducir_stock(self, cantidad):
        """Lógica de negocio: Modifica el atributo stock si hay suficiente"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            return True
        return False


class Cliente:
    """Clase que mapea la tabla 'clientes'"""
    ANONIMO_ID = "C000"
    ANONIMO_NOMBRE = "cliente anonimo"

    def __init__(self, id_cliente, nombre, edad, cedula, direccion, telefono):
        self.id = id_cliente
        self.nombre = nombre
        self.edad = edad
        self.cedula = cedula
        self.direccion = direccion
        self.telefono = telefono

    @classmethod
    def desde_fila_db(cls, fila):
        if not fila:
            return None
        return cls(
            id_cliente=fila["id"], nombre=fila["nombre"], edad=fila["edad"],
            cedula=fila["cedula"], direccion=fila["direccion"], telefono=fila["telefono"]
        )

    @classmethod
    def contar_registrados(cls):
        from models.database import get_db

        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) FROM clientes WHERE id != ?",
            (cls.ANONIMO_ID,),
        ).fetchone()[0]
        conn.close()
        return total

    @classmethod
    def listar_registrados(cls):
        from models.database import get_db

        conn = get_db()
        filas = conn.execute(
            "SELECT * FROM clientes WHERE id != ? ORDER BY nombre",
            (cls.ANONIMO_ID,),
        ).fetchall()
        conn.close()
        return filas

    @classmethod
    def buscar_por_cedula(cls, cedula):
        from models.database import get_db

        conn = get_db()
        fila = conn.execute("SELECT * FROM clientes WHERE cedula = ?", (cedula,)).fetchone()
        conn.close()
        return cls.desde_fila_db(fila)

    @classmethod
    def buscar_por_id(cls, cliente_id):
        from models.database import get_db

        conn = get_db()
        fila = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        conn.close()
        return cls.desde_fila_db(fila)

    @classmethod
    def siguiente_id(cls):
        from models.database import get_db

        conn = get_db()
        max_id = conn.execute(
            "SELECT MAX(CAST(SUBSTR(id, 2) AS INTEGER)) FROM clientes WHERE id != ?",
            (cls.ANONIMO_ID,),
        ).fetchone()[0]
        conn.close()
        return f"C{(max_id or 0) + 1:03}"

    @classmethod
    def datos_desde_empleado(cls, empleado, cedula):
        if not empleado:
            return {
                "cedula": cedula,
                "nombre": "",
                "edad": "",
                "direccion": "",
                "telefono": "",
            }

        return {
            "cedula": cedula,
            "nombre": empleado.nombre or "",
            "edad": empleado.edad or "",
            "direccion": empleado.direccion or "",
            "telefono": empleado.telefono or "",
        }

    @classmethod
    def crear(cls, nombre, edad, cedula, direccion, telefono):
        from models.database import get_db

        nuevo_id = cls.siguiente_id()
        conn = get_db()
        conn.execute(
            """
            INSERT INTO clientes (id, nombre, edad, cedula, direccion, telefono)
            VALUES (?,?,?,?,?,?)
            """,
            (nuevo_id, nombre.lower(), int(edad), int(cedula), direccion, telefono),
        )
        conn.commit()
        conn.close()
        return nuevo_id

    @classmethod
    def eliminar(cls, cliente_id):
        from models.database import get_db

        conn = get_db()
        conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conn.commit()
        conn.close()

    @classmethod
    def asegurar_anonimo(cls):
        from models.database import get_db

        conn = get_db()
        existe = conn.execute(
            "SELECT id FROM clientes WHERE id = ?",
            (cls.ANONIMO_ID,),
        ).fetchone()
        if not existe:
            conn.execute(
                """
                INSERT OR IGNORE INTO clientes
                    (id, nombre, edad, cedula, direccion, telefono)
                VALUES (?,?,?,?,?,?)
                """,
                (cls.ANONIMO_ID, cls.ANONIMO_NOMBRE, 0, 0, "-", "-"),
            )
            conn.commit()
        conn.close()


class Venta:
    """Clase que encapsula operaciones de la tabla 'ventas'."""

    @classmethod
    def contar(cls):
        from models.database import get_db

        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        conn.close()
        return total

    @classmethod
    def ingresos_totales(cls):
        from models.database import get_db

        conn = get_db()
        ingresos = conn.execute("SELECT SUM(total) FROM ventas").fetchone()[0] or 0
        conn.close()
        return ingresos

    @classmethod
    def listar_todas(cls):
        from models.database import get_db

        conn = get_db()
        ventas = conn.execute("SELECT * FROM ventas ORDER BY fecha DESC").fetchall()
        conn.close()
        return ventas

    @classmethod
    def listar_por_vendedor(cls, vendedor):
        from models.database import get_db

        conn = get_db()
        ventas = conn.execute(
            "SELECT * FROM ventas WHERE vendedor = ? ORDER BY fecha DESC",
            (vendedor,),
        ).fetchall()
        conn.close()
        return ventas

    @classmethod
    def contar_por_vendedor(cls, vendedor):
        from models.database import get_db

        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) FROM ventas WHERE vendedor = ?",
            (vendedor,),
        ).fetchone()[0]
        conn.close()
        return total

    @classmethod
    def registrar(cls, juego_id, cliente_id, cantidad, vendedor, fecha):
        from models.database import get_db

        if not cliente_id:
            Cliente.asegurar_anonimo()
            cliente_id = Cliente.ANONIMO_ID

        conn = get_db()
        juego = conn.execute("SELECT * FROM juegos WHERE id = ?", (juego_id,)).fetchone()
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()

        if not juego or not cliente:
            conn.close()
            return {"ok": False, "error": "Juego o cliente no valido.", "juego_id": None}

        if juego["stock"] < cantidad:
            conn.close()
            return {
                "ok": False,
                "error": f"Stock insuficiente. Disponible: {juego['stock']}",
                "juego_id": juego_id,
            }

        total = juego["precio"] * cantidad
        conn.execute(
            """
            INSERT INTO ventas
                (cliente_id, cliente_nombre, juego_id, juego_nombre,
                 cantidad, precio_unitario, total, vendedor, fecha)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                cliente["id"],
                cliente["nombre"],
                juego["id"],
                juego["title"],
                cantidad,
                juego["precio"],
                total,
                vendedor,
                fecha,
            ),
        )
        conn.execute("UPDATE juegos SET stock = stock - ? WHERE id = ?", (cantidad, juego_id))
        conn.commit()
        conn.close()

        etiqueta = "anonimo" if cliente_id == Cliente.ANONIMO_ID else cliente["nombre"]
        return {"ok": True, "total": total, "etiqueta": etiqueta, "juego_id": juego_id}
