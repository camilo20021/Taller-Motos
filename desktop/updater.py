"""Chequeo liviano de actualizaciones: sin auto-descarga ni parches, solo
avisa si hay una versión más nueva disponible para descargar manualmente.

URL_VERSION lo debe configurar el vendedor (un JSON estático tipo
{"latest": "1.1.0", "url": "https://...", "notes": "..."} servido desde
donde quiera: GitHub Releases, su propia página, etc.). Mientras esté vacío,
el chequeo simplemente no hace nada.
"""

import json
import urllib.request

VERSION_ACTUAL = "1.0.0"
URL_VERSION = ""  # Configurar antes de distribuir la app a clientes.


def buscar_actualizacion(timeout: float = 2.0) -> dict | None:
    if not URL_VERSION:
        return None

    try:
        with urllib.request.urlopen(URL_VERSION, timeout=timeout) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - nunca debe romper el arranque de la app
        return None

    if datos.get("latest") and datos["latest"] != VERSION_ACTUAL:
        return datos
    return None
