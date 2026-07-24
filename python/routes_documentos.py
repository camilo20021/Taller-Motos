from flask import Blueprint, flash, redirect, render_template, request, url_for

from .decorators import admin_required
from .extensions import db
from .models import IVA_PORCENTAJE, CierreCaja, Documento, OrdenServicio

documentos_bp = Blueprint("documentos", __name__, url_prefix="/documentos")

PREFIJOS = {"cotizacion": "COT", "factura": "FAC"}


@documentos_bp.route("/")
@admin_required
def listar():
    documentos = Documento.query.order_by(Documento.fecha.desc()).all()
    return render_template("facturacion_listar.html", documentos=documentos)


@documentos_bp.route("/generar/<int:orden_id>", methods=["POST"])
@admin_required
def generar(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)
    tipo = request.form.get("tipo")
    if tipo not in PREFIJOS:
        flash("Tipo de documento inválido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    subtotal = orden.subtotal_total
    iva = round(subtotal * IVA_PORCENTAJE, 2)
    documento = Documento(
        orden_id=orden.id,
        tipo=tipo,
        subtotal=subtotal,
        iva=iva,
        total=subtotal + iva,
        estado="pendiente",
        numero="PENDIENTE",
    )
    db.session.add(documento)
    db.session.flush()
    documento.numero = f"{PREFIJOS[tipo]}-{documento.id:06d}"
    db.session.commit()

    flash(f"{'Cotización' if tipo == 'cotizacion' else 'Factura'} {documento.numero} generada.", "success")
    return redirect(url_for("documentos.detalle", documento_id=documento.id))


@documentos_bp.route("/<int:documento_id>")
@admin_required
def detalle(documento_id):
    documento = Documento.query.get_or_404(documento_id)
    return render_template("factura_detalle.html", documento=documento)


@documentos_bp.route("/<int:documento_id>/pagar", methods=["POST"])
@admin_required
def marcar_pagada(documento_id):
    documento = Documento.query.get_or_404(documento_id)
    documento.estado = "pagada"

    caja_abierta = CierreCaja.query.filter_by(fecha_cierre=None).first()
    if caja_abierta is not None:
        documento.cierre_caja_id = caja_abierta.id

    db.session.commit()
    flash(f"{documento.numero} marcada como pagada.", "success")
    return redirect(url_for("documentos.detalle", documento_id=documento.id))
