# Gestión de Taller — aplicación de escritorio para talleres de motos

Aplicación de escritorio para Windows (no una página web) para administrar un
taller de motos. Cada taller que la instala tiene su propia base de datos
local (SQLite), funciona sin internet, **los mecánicos entran solo
eligiendo su nombre de una lista (sin contraseña)** — el administrador sí
necesita contraseña, para que nadie más entre a inventario/caja/facturación
— y se activa con una licencia que tú mismo generas, pensada para venderse
como producto a distintos talleres, no solo para un único negocio. Sin
comprar la licencia, funciona igual durante 1 mes de prueba.

Controla:

- **Clientes y motos**: nombre, cédula, celular, correo y las motos asociadas a cada cliente.
- **Órdenes de servicio**: ingreso y salida de motos, estado (recibida → diagnóstico → en reparación → esperando repuesto → terminado → entregado), diagnóstico y observaciones.
- **Notificación automática por correo**: al registrar el ingreso de una moto y cuando se marca una orden como "terminado", se envía un correo al cliente (si el correo del taller está configurado).
- **Inventario de repuestos**: stock, stock mínimo, entradas/salidas, y descuento automático de stock cuando se usa un repuesto en una orden.
- **Cotizaciones y facturas**: generadas a partir de los repuestos y mano de obra registrados en cada orden, con IVA (19%) calculado.
- **Cierre de caja**: se abre la caja con una base inicial y se cierra contando el efectivo real; el sistema calcula lo esperado (base + ventas pagadas) y muestra el sobrante o faltante.

## Cómo está construida

Por dentro sigue siendo una aplicación web Flask (con SQLite como base de
datos), pero se ejecuta empaquetada como programa de escritorio:
[pywebview](https://pywebview.flowrl.com/) arranca ese servidor Flask en un
hilo local y lo muestra en una ventana nativa de Windows — no hay navegador
visible, ni consola, ni necesidad de instalar Python en la máquina del
cliente final.

```
Taller-Motos/
├── run.py                    Servidor de desarrollo (navegador, http://127.0.0.1:5000)
├── desktop_entry.py           Punto de entrada real del .exe empaquetado
├── requirements.txt            Dependencias de producción
├── requirements-dev.txt         + pywebview, pyinstaller (para compilar el .exe)
├── python/                      Backend Flask (idéntico en dev y en escritorio)
│   ├── __init__.py                Fábrica de la app: blueprints, siembra inicial, asistente de setup
│   ├── config.py                   Config (ruta de datos, correo, nombre del producto)
│   ├── models.py                    Modelos SQLAlchemy
│   ├── decorators.py                 @admin_required
│   ├── crypto_utils.py                Cifra/descifra la contraseña de correo guardada
│   ├── email_utils.py                 Envío de correo "moto ingresada"/"lista" (best-effort, vía API de Brevo)
│   ├── routes_*.py                     Un blueprint por sección (auth, clientes, órdenes...)
│   ├── routes_setup.py                  Asistente de primer arranque (taller + admin)
│   ├── routes_ajustes.py                 Ajustes de correo (API key de Brevo propia de cada taller)
│   ├── routes_respaldo.py                Exportar respaldo manual
│   ├── templates/                         Las plantillas HTML (Jinja2)
│   └── static/{css,js}/                    Estilos e interacción del lado del cliente
├── desktop/                       Capa nativa de escritorio
│   ├── main.py                      Orquesta todo al abrir el programa
│   ├── appdata.py                    Rutas bajo %LOCALAPPDATA%\TallerMotos
│   ├── server.py                      Arranca Flask (waitress) en un puerto local libre
│   ├── single_instance.py              Evita abrir el programa dos veces
│   ├── license_check.py                 Valida la licencia (.lic) sin necesitar internet
│   ├── license_public_key.py             Clave pública para verificar licencias
│   ├── activation_window.py               Pantalla de activación cuando falta licencia
│   ├── backup.py                           Respaldo automático (al cerrar) y manual
│   └── updater.py                           Aviso simple de nueva versión disponible
├── tools/
│   └── generate_license.py         Script del VENDEDOR para firmar licencias (no se distribuye)
└── packaging/
    ├── TallerMotos.spec             PyInstaller (genera dist/TallerMotos/)
    ├── installer.iss                 Inno Setup (genera el instalador .exe final)
    └── assets/app.ico                 Ícono de la app (agrega el tuyo antes de vender)
```

## Requisitos

- Python 3.10 o superior (para desarrollar / compilar — el cliente final no necesita instalar Python).
- Windows 10/11 con "Microsoft Edge WebView2 Runtime" (viene preinstalado en la gran mayoría de equipos; el instalador avisa si falta).

## Modo desarrollo (navegador)

Para programar/probar cambios rápido, sin empaquetar nada:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Abre `http://127.0.0.1:5000`. La primera vez que arranca con la base de
datos vacía, crea automáticamente el taller y el administrador inicial con
los datos que definas en `.env` (`TALLER_NOMBRE`, `ADMIN_NOMBRE`,
`ADMIN_PASSWORD`). Los mecánicos que agregues después no usan contraseña —
solo el administrador la necesita.

## Modo escritorio (ventana nativa, sin empaquetar)

Para probar la experiencia real de escritorio directamente con Python, sin
compilar un .exe todavía:

```bash
pip install -r requirements-dev.txt
python desktop_entry.py
```

En este modo **no** se usa `.env` para crear el taller: la primera vez se
abre un asistente de configuración inicial (nombre del taller + tu cuenta de
administrador, con contraseña) directamente en la ventana de la app. Los
datos se guardan en `%LOCALAPPDATA%\TallerMotos\` en vez de en la carpeta
del proyecto.

## Compilar el instalador para vender

1. Agrega tu logo como `packaging/assets/app.ico` (ícono de Windows) — todavía no tiene uno propio.
2. Genera el ejecutable:
   ```bash
   pyinstaller packaging/TallerMotos.spec --distpath dist --workpath build
   ```
   Esto crea `dist/TallerMotos/TallerMotos.exe` y todo lo que necesita a su lado.
3. Compila el instalador con [Inno Setup](https://jrsoftware.org/isinfo.php):
   ```bash
   ISCC.exe packaging/installer.iss
   ```
   (o abre `packaging/installer.iss` en el editor de Inno Setup y presiona "Compilar"). Obtienes `dist-installer/TallerMotosSetup.exe`, listo para entregarle al cliente — instala en silencio, crea accesos directos, revisa si falta WebView2, y desinstala sin borrar los datos del taller.

Cada nueva versión debe compilarse igual y mantener el mismo `AppId` en
`installer.iss` para que el instalador actualice en vez de duplicar.

## Licenciamiento (vender copias a otros talleres)

No hay servidor de licencias: cada licencia es un archivo `.lic` firmado
digitalmente (Ed25519) que tú generas.

1. La primera vez que corras `tools/generate_license.py` se crea
   automáticamente tu clave privada en `tools/private_key.pem` — **este
   archivo es tuyo, nunca lo compartas ni lo subas a git** (ya está en
   `.gitignore`). También te mostrará la clave pública correspondiente:
   confirma que sea la misma que ya está en `desktop/license_public_key.py`
   antes de vender (si es la primera vez, cópiala ahí).
2. Para cada cliente nuevo:
   ```bash
   python tools/generate_license.py
   ```
   Ingresa el nombre del taller, los días de validez y los cupos. Se genera
   un archivo `<taller>-activation.lic` — envíaselo al cliente (por correo,
   por ejemplo).
3. El cliente, desde la pantalla de activación de la app, selecciona ese
   archivo `.lic` y queda activado. Todo funciona sin conexión a internet.

Mientras no haya licencia activa, la app funciona igual durante **1 mes (30
días) de prueba** desde el primer arranque; después de eso pide activarla
con un archivo `.lic` para seguir usándose.

## Si un cliente se queda trabado sin poder entrar (olvidó la contraseña de administrador)

Como no hay "olvidé mi contraseña" dentro de la app (sería un hueco de
seguridad), esto se resuelve por soporte: entra a la PC del cliente (remoto
o en persona) con este proyecto disponible ahí, y corre:

```bash
python tools/reset_admin_password.py
```

Por defecto busca la carpeta de datos real de esa instalación
(`%LOCALAPPDATA%\TallerMotos`), te muestra los administradores registrados y
te deja ponerle una contraseña nueva sin necesitar la vieja.

## Respaldo de datos

Cada taller es dueño de su propia base de datos (no hay una nube por
detrás), así que los respaldos importan:

- **Automático**: se guarda una copia en `%LOCALAPPDATA%\TallerMotos\backups\`
  cada vez que se cierra el programa (se conservan los últimos 10).
- **Manual**: desde **Usuarios → Exportar respaldo...** se puede guardar una
  copia donde el usuario elija (por ejemplo, en una USB o en la nube personal).

## Sin contraseña para el mecánico, con contraseña para el administrador

Como la información es local (vive solo en la PC del taller), no hay
pantalla de correo/contraseña de entrada: al abrir el programa se muestra
una lista de "¿Quién eres?" con los nombres de las personas registradas.
Si eliges un **mecánico**, entras directo. Si eliges el **Administrador**,
te pide la contraseña de esa cuenta — así un mecánico no puede simplemente
elegir "Administrador" de la lista y ver inventario, facturación, caja o la
gestión de usuarios:

## Roles de usuario

| Sección | Administrador | Mecánico |
|---|---|---|
| Panel / dashboard | ✅ completo | ✅ (sin datos de inventario) |
| Ver clientes y motos | ✅ | ✅ |
| Crear / editar / eliminar clientes | ✅ | ❌ |
| Registrar / modificar motos | ✅ | ✅ |
| Órdenes de servicio (ingreso, estado, diagnóstico, repuestos usados) | ✅ | ✅ |
| Inventario (crear repuestos, editar precios, movimientos manuales) | ✅ | ❌ |
| Cotizaciones / facturas | ✅ | ❌ |
| Cierre de caja | ✅ | ❌ |
| Gestión de usuarios | ✅ | ❌ |

Si un mecánico intenta entrar a una sección restringida, ve una página de
"Acceso restringido" en vez de romperse.

## Configurar el envío de correos ("moto ingresada" / "moto lista")

Al registrar el ingreso de una moto y cuando una orden pasa a **"Terminado"**,
el sistema intenta enviar un correo automático al cliente. Los correos se
mandan a través de **[Brevo](https://www.brevo.com)** (antes Sendinblue),
no de Gmail: Google restringe cada vez más las "contraseñas de aplicación"
(muchas cuentas nuevas o con llaves de acceso ya ni las dejan generar), así
que un servicio con una sola API key es más confiable para un producto que
se vende a distintos talleres.

Cada taller configura esto **desde dentro de la app**, en **Ajustes de
correo** (solo lo ve el administrador) — no hay que editar ningún archivo:

1. Cuenta gratis en brevo.com (300 correos/día gratis, sin tarjeta).
2. En su panel: **SMTP & API → API Keys** → generar una → pegarla en Ajustes de correo.
3. En su panel: **Senders & IP → Senders** → verificar el correo que van a usar como remitente (Brevo manda un enlace de confirmación) — sin verificarlo, el envío falla.

La API key queda cifrada en la base de datos, nunca en texto plano. Hay un
botón para mandar un correo de prueba y confirmar que quedó bien.

> **Primer envío de cada taller**: Brevo suele rechazar el primer correo con
> un error de "IP no reconocida" (protección de cuentas nuevas). Hay que
> entrar a `app.brevo.com/security/authorised_ips` y desactivar la
> autorización de IP (o agregar la IP que indique el error). Como cada
> taller manda desde su propia PC/IP, esto le va a pasar a **cada cliente
> nuevo** la primera vez — ya quedó explicado dentro de la propia pantalla
> de Ajustes de correo para que no se atoren.

En modo desarrollo, si `.env` trae `BREVO_API_KEY`/`MAIL_REMITENTE_CORREO`,
esos valores se precargan automáticamente la primera vez (para no tener que
llenarlos a mano mientras programas) — en producción no se usan.

Si el cliente no tiene correo registrado, o el envío falla (credenciales
incorrectas, sin internet, etc.), la orden se actualiza igual — el sistema
solo muestra un aviso, nunca se rompe por eso.

## Cómo funciona el cierre de caja

1. El administrador **abre la caja** al iniciar el turno/día, ingresando la base inicial (el efectivo con el que arranca).
2. Mientras la caja está abierta, cada factura que se marca como **pagada** queda ligada automáticamente a esa caja.
3. Al final del turno, el administrador **cierra la caja**: cuenta el efectivo físico y lo ingresa.
4. El sistema calcula:
   - **Esperado** = base inicial + ventas pagadas durante ese turno.
   - **Diferencia** = efectivo contado − esperado (positivo = sobrante, negativo = faltante).
5. Queda guardado en el historial de cierres, con quién abrió y quién cerró la caja.

Solo puede haber una caja abierta a la vez.

## Flujo típico de uso

1. Al abrir la app por primera vez, se configura el taller y el nombre del administrador (asistente de configuración inicial).
2. El administrador agrega a los mecánicos (`Usuarios → + Nueva persona`) — solo con su nombre, sin contraseña.
3. El administrador registra un cliente con sus datos (nombre, cédula, celular, correo).
4. Se registra la moto del cliente (placa, marca, modelo...) — esto lo puede hacer el administrador o el mecánico.
5. Cuando el cliente trae la moto, se crea una **orden de servicio** (esto es el "ingreso" de la moto) — lo hace el mecánico.
6. El mecánico va actualizando el estado de la orden y el diagnóstico.
7. Se agregan los repuestos usados (descuentan del inventario automáticamente) y la mano de obra.
8. Al terminar la reparación, se cambia el estado a **"Terminado"** → el cliente recibe un correo automático (si el correo del taller está configurado).
9. El administrador genera la cotización o factura, y la marca como pagada cuando corresponda (queda ligada a la caja abierta).
10. Al entregar la moto, se cambia el estado a **"Entregada"** (esto es la "salida" de la moto).
11. Al final del turno, el administrador cierra la caja y verifica que cuadre.
