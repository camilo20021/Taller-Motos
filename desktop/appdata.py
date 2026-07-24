"""Rutas de datos de la aplicación de escritorio.

Todo lo que un taller necesita conservar (base de datos, licencia, respaldos,
logs) vive bajo %LOCALAPPDATA%\\TallerMotos, NO junto al ejecutable — así
sobrevive a reinstalaciones/actualizaciones y no requiere permisos de
administrador.
"""

import os
import secrets
from pathlib import Path

APP_FOLDER_NAME = "TallerMotos"


def get_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    data_dir = Path(base) / APP_FOLDER_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("license", "backups", "logs"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    return data_dir


def license_dir() -> Path:
    return get_data_dir() / "license"


def backups_dir() -> Path:
    return get_data_dir() / "backups"


def logs_dir() -> Path:
    return get_data_dir() / "logs"


def db_path() -> Path:
    return get_data_dir() / "taller.db"


def marca_primer_arranque_path() -> Path:
    return get_data_dir() / "primer_arranque.txt"


def obtener_secret_key() -> str:
    """Clave secreta única por instalación (firma las sesiones y cifra la
    contraseña de correo guardada). Se genera una sola vez y se reutiliza en
    cada arranque -- si no persistiera, las sesiones se invalidarían y la
    contraseña de correo guardada quedaría ilegible en cada reinicio."""
    ruta = get_data_dir() / "secret_key.txt"
    if not ruta.exists():
        ruta.write_text(secrets.token_hex(32), encoding="utf-8")
    return ruta.read_text(encoding="utf-8").strip()
