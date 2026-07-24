from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .decorators import admin_required
from .extensions import db
from .models import CierreCaja

caja_bp = Blueprint("caja", __name__, url_prefix="/caja")


@caja_bp.route("/")
@admin_required
def index():
    caja_abierta = CierreCaja.query.filter_by(fecha_cierre=None).first()
    historial = (
        CierreCaja.query.filter(CierreCaja.fecha_cierre.isnot(None))
        .order_by(CierreCaja.fecha_cierre.desc())
        .all()
    )
    return render_template("caja.html", caja_abierta=caja_abierta, historial=historial)


@caja_bp.route("/abrir", methods=["POST"])
@admin_required
def abrir():
    if CierreCaja.query.filter_by(fecha_cierre=None).first() is not None:
        flash("Ya hay una caja abierta.", "error")
        return redirect(url_for("caja.index"))

    caja = CierreCaja(
        taller_id=current_user.taller_id,
        abierto_por_id=current_user.id,
        monto_inicial=float(request.form.get("monto_inicial") or 0),
    )
    db.session.add(caja)
    db.session.commit()
    flash("Caja abierta.", "success")
    return redirect(url_for("caja.index"))


@caja_bp.route("/<int:caja_id>/cerrar", methods=["POST"])
@admin_required
def cerrar(caja_id):
    caja = CierreCaja.query.get_or_404(caja_id)
    if caja.fecha_cierre is not None:
        flash("Esta caja ya fue cerrada.", "error")
        return redirect(url_for("caja.index"))

    caja.monto_contado = float(request.form.get("monto_contado") or 0)
    caja.observaciones = request.form.get("observaciones", "").strip() or None
    caja.fecha_cierre = datetime.utcnow()
    caja.cerrado_por_id = current_user.id
    db.session.commit()
    flash("Caja cerrada correctamente.", "success")
    return redirect(url_for("caja.index"))
