from flask import Blueprint, flash, redirect, url_for

from .decorators import admin_required

respaldo_bp = Blueprint("respaldo", __name__, url_prefix="/respaldo")


@respaldo_bp.route("/exportar", methods=["POST"])
@admin_required
def exportar():
    """Exporta un respaldo manual de la base de datos.

    Solo funciona en la versión de escritorio (necesita la ventana nativa de
    pywebview para el diálogo "Guardar como..."). En el servidor de
    desarrollo simplemente avisa que no está disponible.
    """
    try:
        import webview

        if not webview.windows:
            raise RuntimeError("sin ventana de escritorio activa")

        from desktop import backup as desktop_backup

        destino = webview.windows[0].create_file_dialog(
            webview.SAVE_DIALOG, save_filename="respaldo_taller.db"
        )
        if not destino:
            flash("Exportación cancelada.", "info")
        else:
            ruta = destino if isinstance(destino, str) else destino[0]
            ok, mensaje = desktop_backup.exportar_a(ruta)
            flash(mensaje, "success" if ok else "error")
    except Exception:
        flash("Exportar respaldo solo está disponible en la versión de escritorio.", "error")

    return redirect(url_for("usuarios.listar"))
