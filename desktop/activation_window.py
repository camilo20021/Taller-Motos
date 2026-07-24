"""Pantalla nativa de activación de licencia (se muestra antes de la ventana
principal cuando no hay una licencia válida y ya se acabó el periodo de gracia).
"""

from pathlib import Path

import webview

from . import license_check

RUTA_HTML = Path(__file__).parent / "assets" / "activacion.html"


class _ActivationAPI:
    def __init__(self):
        self.activada = False

    def elegir_archivo(self):
        ventana = webview.windows[0]
        resultado = ventana.create_file_dialog(
            webview.OPEN_DIALOG, file_types=("Archivo de licencia (*.lic)",)
        )
        if not resultado:
            return {"ok": False, "mensaje": "No se seleccionó ningún archivo."}

        ok, mensaje = license_check.activar_licencia(resultado[0])
        if ok:
            self.activada = True
        return {"ok": ok, "mensaje": mensaje}

    def cerrar(self):
        webview.windows[0].destroy()


def mostrar_pantalla_activacion() -> bool:
    api = _ActivationAPI()
    webview.create_window(
        "Activar licencia — Gestión de Taller",
        str(RUTA_HTML),
        width=440,
        height=380,
        resizable=False,
        js_api=api,
    )
    webview.start()
    return api.activada
