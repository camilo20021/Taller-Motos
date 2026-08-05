import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from .decorators import admin_required
from .extensions import db
from .models import Taller
from .utils import parse_float

ajustes_bp = Blueprint("ajustes", __name__, url_prefix="/ajustes")

EXTENSIONES_LOGO = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@ajustes_bp.route("/taller", methods=["GET", "POST"])
@admin_required
def taller():
    taller = Taller.query.first()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre del taller es obligatorio.", "error")
            return redirect(url_for("ajustes.taller"))

        taller.nombre = nombre
        taller.nit = request.form.get("nit", "").strip() or None
        taller.direccion = request.form.get("direccion", "").strip() or None
        taller.telefono = request.form.get("telefono", "").strip() or None

        # El IVA se ingresa como porcentaje (ej. 19) y se guarda como fracción.
        iva = parse_float(request.form.get("iva_porcentaje"), 19)
        iva = min(max(iva, 0), 100)
        taller.iva_porcentaje = round(iva / 100, 4)

        # Logo opcional.
        archivo = request.files.get("logo")
        if archivo and archivo.filename:
            ext = os.path.splitext(secure_filename(archivo.filename))[1].lower()
            if ext not in EXTENSIONES_LOGO:
                flash("El logo debe ser una imagen (png, jpg, webp o gif).", "error")
                return redirect(url_for("ajustes.taller"))
            destino = os.path.join(current_app.config["INSTANCE_DIR"], f"logo{ext}")
            archivo.save(destino)
            taller.logo = f"logo{ext}"

        db.session.commit()
        flash("Datos del taller guardados.", "success")
        return redirect(url_for("ajustes.taller"))

    return render_template("ajustes_taller.html", taller=taller)


@ajustes_bp.route("/logo")
def logo():
    """Sirve el logo del taller desde la carpeta de datos (escribible incluso
    en la versión empaquetada, a diferencia de /static)."""
    taller = Taller.query.first()
    if not taller or not taller.logo:
        return ("", 404)
    return send_from_directory(current_app.config["INSTANCE_DIR"], taller.logo)
