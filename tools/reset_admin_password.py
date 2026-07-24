"""Herramienta de SOPORTE para resetear la contraseña de un administrador
que quedó trabado (perdió/olvidó su contraseña y no hay otro admin activo).

Cómo usarla: entra a la PC del cliente (remoto, ej. AnyDesk/TeamViewer, o en
persona), y con este mismo proyecto instalado ahí (o copiado temporalmente),
corre:

    python tools/reset_admin_password.py

Por defecto apunta a la carpeta de datos real de la instalación de
escritorio (%LOCALAPPDATA%\\TallerMotos). Si necesitas apuntar a otra carpeta
(por ejemplo, revisando un respaldo), pásala como argumento:

    python tools/reset_admin_password.py "C:\\ruta\\a\\la\\carpeta"

No pide la contraseña vieja -- accede directo a la base de datos, así que
solo debe usarse con el cliente al tanto (por soporte).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os

if len(sys.argv) > 1:
    os.environ["TALLER_DATA_DIR"] = sys.argv[1]
else:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        print("No se encontró %LOCALAPPDATA%. Pasa la ruta de datos como argumento.")
        sys.exit(1)
    os.environ["TALLER_DATA_DIR"] = str(Path(local_appdata) / "TallerMotos")

os.environ["AUTO_SEED_INICIAL"] = "false"
os.environ.setdefault("MAIL_SUPPRESS_SEND", "true")

from python import create_app
from python.extensions import db
from python.models import Usuario


def main():
    app = create_app()
    with app.app_context():
        print(f"Usando base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}\n")

        admins = Usuario.query.filter_by(rol="admin").order_by(Usuario.nombre.asc()).all()
        if not admins:
            print("No hay ninguna cuenta de administrador en esta base de datos.")
            return

        print("Cuentas de administrador encontradas:")
        for admin in admins:
            estado = "activa" if admin.activo else "INACTIVA"
            print(f"  [{admin.id}] {admin.nombre} ({estado})")

        elegido = input("\nID del administrador al que le vas a cambiar la contraseña: ").strip()
        usuario = Usuario.query.get(elegido)
        if usuario is None or usuario.rol != "admin":
            print("Ese ID no corresponde a una cuenta de administrador.")
            return

        if not usuario.activo:
            confirmar = input(f"{usuario.nombre} está INACTIVA. ¿Reactivarla también? (s/n): ").strip().lower()
            if confirmar == "s":
                usuario.activo = True

        nueva = input(f"Nueva contraseña para {usuario.nombre} (mínimo 4 caracteres): ").strip()
        if len(nueva) < 4:
            print("La contraseña debe tener al menos 4 caracteres. Nada se guardó.")
            return

        usuario.set_password(nueva)
        db.session.commit()
        print(f"\nListo. La contraseña de {usuario.nombre} fue actualizada.")


if __name__ == "__main__":
    main()
