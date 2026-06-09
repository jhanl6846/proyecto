# Tienda de Juegos Mejorada

Aplicacion Flask para administrar una tienda de juegos: autenticacion por roles, catalogo, clientes, empleados, ventas, descuentos e inventario.

## Funciones principales

- Login de empleados con roles de administrador y vendedor.
- Panel de inicio con tarjetas clicables.
- Menu lateral desplegable para navegar sin barra superior.
- Catalogo cargado desde la API de FreeToGame cuando la tabla `juegos` esta vacia.
- Registro de ventas con descuento automatico de stock.
- Cliente anonimo `C000` para ventas sin registro.
- El cliente anonimo no se cuenta como cliente registrado.
- Documentacion Swagger en `http://localhost:3000/apidocs`.

## Estructura

```text
app.py                  Punto de entrada de Flask y configuracion Swagger
models/database.py      Conexion, ruta e inicializacion de SQLite
models/entidades.py     Clases de dominio y persistencia: Empleado, Juego, Cliente y Venta
routes/                 Blueprints por modulo
templates/              Vistas HTML/Jinja
static/css/main.css     Estilos de la interfaz
static/js/main.js       Interacciones del menu y flashes
utils/clientes.py       Helpers compartidos de clientes
utils/decorators.py     Decoradores de autenticacion y permisos
```

## Organizacion con clases

Las clases en `models/entidades.py` tienen protagonismo en la logica de datos:

- `Empleado`: autenticar/buscar empleados, listar, contar, crear y eliminar.
- `Cliente`: buscar por cedula, listar registrados, contar registrados, crear, eliminar y asegurar el cliente anonimo.
- `Juego`: buscar, contar, crear, eliminar y aplicar descuentos.
- `Venta`: listar ventas, contar ventas, calcular ingresos y registrar ventas descontando stock.

Las rutas se encargan principalmente de recibir formularios, mostrar mensajes y redirigir. La lectura/escritura de base de datos se concentra progresivamente en las clases.

## Ejecutar

```powershell
.\proyecto\Scripts\python.exe .\app.py
```

La aplicacion corre por defecto en:

```text
http://localhost:3000
```

Credenciales iniciales:

```text
ID: E001
Contrasena: 123456
Rol: administrador
```

## Base de datos

La base de datos se guarda en `tienda.db`. La ruta se define en `models/database.py` y puede cambiarse con la variable de entorno `TIENDA_DB_PATH`.

Si `tienda.db` se borra, la app vuelve a crear las tablas y el administrador inicial. El catalogo se recarga desde FreeToGame cuando la tabla `juegos` queda vacia.

## Cliente anonimo

`C000` se usa para registrar ventas cuando el comprador no quiere registrarse. Este cliente:

- No aparece en listas de clientes registrados.
- No se cuenta en los dashboards.
- No afecta el siguiente ID de cliente real.

## Documentacion de rutas

Swagger lee la documentacion desde los docstrings de las vistas. Al agregar o modificar una ruta, actualiza el docstring en el mismo formato `---` para que aparezca en `/apidocs`.
