"""Punto de entrada de la aplicación de escritorio.

Flujo: evita una segunda instancia -> fija la carpeta de datos en
%LOCALAPPDATA% -> valida la licencia (con periodo de gracia) -> arranca Flask
en un hilo local -> abre la ventana nativa con pywebview -> respalda la base
de datos al cerrar.
"""

import ctypes
import os
import sys

import webview

from . import appdata, backup, license_check, single_instance
from .server import iniciar_servidor, puerto_libre

TITULO = "Gestión de Taller"


def _mensaje(texto: str, titulo: str = TITULO) -> None:
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, texto, titulo, 0x40)
    else:
        print(f"[{titulo}] {texto}")


def _preparar_entorno() -> None:
    data_dir = appdata.get_data_dir()
    os.environ["TALLER_DATA_DIR"] = str(data_dir)
    os.environ["AUTO_SEED_INICIAL"] = "false"
    # Clave propia de esta instalación (no la compartida por defecto del
    # código fuente) -- firma las sesiones y cifra la contraseña de correo.
    os.environ["SECRET_KEY"] = appdata.obtener_secret_key()


def _resolver_licencia() -> bool:
    """Devuelve True si se puede continuar (licencia válida o en gracia)."""
    estado = license_check.verificar()

    if estado.valida:
        return True

    if estado.en_gracia:
        _mensaje(
            f"{estado.mensaje}\n\nPuedes seguir usando el programa mientras activas tu licencia.",
        )
        return True

    from .activation_window import mostrar_pantalla_activacion

    if mostrar_pantalla_activacion():
        return True

    _mensaje("No se activó ninguna licencia. El programa se cerrará.")
    return False


def _lanzar_aplicacion_principal() -> None:
    from python import create_app

    app = create_app()

    puerto = puerto_libre()
    iniciar_servidor(app, puerto)
    url = f"http://127.0.0.1:{puerto}/"

    ventana = webview.create_window(
        TITULO,
        url,
        width=1280,
        height=820,
        min_size=(1024, 700),
    )
    ventana.events.closing += lambda: backup.respaldo_automatico()

    webview.start()


def main() -> None:
    if single_instance.ya_hay_una_instancia():
        _mensaje(f"{TITULO} ya está abierto.")
        return

    _preparar_entorno()

    if not _resolver_licencia():
        return

    _lanzar_aplicacion_principal()


if __name__ == "__main__":
    main()
