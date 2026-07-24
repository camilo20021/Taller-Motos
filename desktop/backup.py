"""Respaldo de la base de datos SQLite (cada taller es dueño de sus propios
datos, así que no hay una nube de respaldo detrás — esto es todo lo que hay)."""

import sqlite3
from pathlib import Path

from . import appdata

MAX_RESPALDOS_AUTOMATICOS = 10


def _copiar(origen: Path, destino: Path) -> None:
    # Se usa la API de respaldo de sqlite3 (no una copia de archivo cruda)
    # para que funcione de forma segura aunque la base esté en uso.
    con_origen = sqlite3.connect(str(origen))
    con_destino = sqlite3.connect(str(destino))
    try:
        con_origen.backup(con_destino)
    finally:
        con_origen.close()
        con_destino.close()


def respaldo_automatico() -> Path | None:
    origen = appdata.db_path()
    if not origen.exists():
        return None

    from datetime import datetime

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = appdata.backups_dir() / f"taller_{marca}.db"
    _copiar(origen, destino)
    _rotar_respaldos()
    return destino


def _rotar_respaldos() -> None:
    respaldos = sorted(
        appdata.backups_dir().glob("taller_*.db"), key=lambda p: p.stat().st_mtime
    )
    exceso = len(respaldos) - MAX_RESPALDOS_AUTOMATICOS
    for viejo in respaldos[: max(exceso, 0)]:
        viejo.unlink(missing_ok=True)


def exportar_a(ruta_destino: str) -> tuple[bool, str]:
    origen = appdata.db_path()
    if not origen.exists():
        return False, "No hay base de datos para respaldar todavía."
    try:
        _copiar(origen, Path(ruta_destino))
        return True, f"Respaldo guardado en {ruta_destino}."
    except Exception as error:  # noqa: BLE001
        return False, f"No se pudo exportar el respaldo ({error})."
