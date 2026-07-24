from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import crypto_utils
from .decorators import admin_required
from .email_utils import enviar_prueba
from .extensions import db
from .models import Taller

ajustes_bp = Blueprint("ajustes", __name__, url_prefix="/ajustes")


@ajustes_bp.route("/correo", methods=["GET", "POST"])
@admin_required
def correo():
    taller = Taller.query.first()

    if request.method == "POST":
        taller.mail_remitente_correo = request.form.get("mail_remitente_correo", "").strip() or None
        taller.mail_remitente_nombre = (
            request.form.get("mail_remitente_nombre", "").strip() or taller.nombre
        )

        api_key_nueva = request.form.get("brevo_api_key", "").strip()
        if api_key_nueva:
            taller.brevo_api_key_cifrada = crypto_utils.cifrar(api_key_nueva)

        db.session.commit()
        flash("Configuración de correo guardada.", "success")
        return redirect(url_for("ajustes.correo"))

    return render_template("ajustes_correo.html", taller=taller)


@ajustes_bp.route("/correo/probar", methods=["POST"])
@admin_required
def probar_correo():
    destinatario = request.form.get("destinatario", "").strip()
    if not destinatario:
        flash("Escribe un correo de destino para la prueba.", "error")
        return redirect(url_for("ajustes.correo"))

    _ok, mensaje = enviar_prueba(destinatario)
    flash(mensaje, "success" if _ok else "error")
    return redirect(url_for("ajustes.correo"))
