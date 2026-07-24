import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Nombre del producto (marca de la aplicación), distinto del nombre del
# taller de cada cliente que se muestra dentro de la app.
APP_PRODUCTO = "Gestión de Taller"


def _resolve_instance_dir() -> Path:
    data_dir = os.environ.get("TALLER_DATA_DIR")
    instance_dir = Path(data_dir) if data_dir else BASE_DIR / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)
    return instance_dir


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

    INSTANCE_DIR = _resolve_instance_dir()
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(INSTANCE_DIR / 'taller.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}

    # Nota: la configuración de correo del taller (MAIL_SERVER, etc.) ya NO
    # vive aquí -- se guarda cifrada en la base de datos de cada taller
    # (columnas mail_* en el modelo Taller), editable desde Ajustes → Correo
    # dentro de la propia app. Las variables MAIL_* en .env solo sirven para
    # precargarla automáticamente en el primer arranque de desarrollo.

    # Solo se usan la primera vez que arranca la app con la base de datos
    # vacía, para crear el taller y la cuenta administradora inicial.
    TALLER_NOMBRE = os.environ.get("TALLER_NOMBRE", "Mi Taller")
    TALLER_NIT = os.environ.get("TALLER_NIT", "")
    TALLER_DIRECCION = os.environ.get("TALLER_DIRECCION", "")
    TALLER_TELEFONO = os.environ.get("TALLER_TELEFONO", "")

    ADMIN_NOMBRE = os.environ.get("ADMIN_NOMBRE", "Administrador")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "cambiar123")

    # En modo desarrollo (python run.py) se siembra el taller/admin desde las
    # variables de arriba automáticamente. La versión de escritorio apaga esto
    # (AUTO_SEED_INICIAL=false) y usa en su lugar el asistente interactivo de
    # primer arranque (ver python/routes_setup.py) para no tener que editar
    # archivos .env.
    AUTO_SEED_INICIAL = os.environ.get("AUTO_SEED_INICIAL", "true").lower() == "true"
