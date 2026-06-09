from models.entidades import Cliente, Empleado

CLIENTE_ANONIMO_ID = Cliente.ANONIMO_ID
CLIENTE_ANONIMO_NOMBRE = Cliente.ANONIMO_NOMBRE


def contar_clientes_registrados(conn=None):
    return Cliente.contar_registrados()


def listar_clientes_registrados(conn=None):
    return Cliente.listar_registrados()


def siguiente_cliente_id(conn=None):
    return Cliente.siguiente_id()


def buscar_cliente_por_cedula(conn, cedula):
    return Cliente.buscar_por_cedula(cedula)


def buscar_empleado_por_cedula(conn, cedula):
    return Empleado.buscar_por_cedula(cedula)


def datos_cliente_desde_empleado(empleado, cedula):
    return Cliente.datos_desde_empleado(empleado, cedula)


def asegurar_cliente_anonimo(conn=None):
    Cliente.asegurar_anonimo()
