import csv
import io
from datetime import date, timedelta

from flask import Blueprint, Response, render_template, request
from sqlalchemy import func

from .decorators import admin_required
from .extensions import db
from .models import (
    Documento,
    ItemRepuestoOrden,
    OrdenServicio,
    Usuario,
)

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _rango():
    """Lee desde/hasta de la query; por defecto, los últimos 30 días."""
    hoy = date.today()
    try:
        hasta = date.fromisoformat(request.args.get("hasta") or hoy.isoformat())
    except ValueError:
        hasta = hoy
    try:
        desde = date.fromisoformat(request.args.get("desde") or (hoy - timedelta(days=30)).isoformat())
    except ValueError:
        desde = hoy - timedelta(days=30)
    return desde, hasta


def _datos(desde, hasta):
    d, h = desde.isoformat(), hasta.isoformat()

    ordenes_ingresadas = (
        db.session.query(func.count(OrdenServicio.id))
        .filter(func.date(OrdenServicio.fecha_ingreso).between(d, h))
        .scalar()
    )
    ordenes_entregadas = (
        db.session.query(func.count(OrdenServicio.id))
        .filter(OrdenServicio.estado == "entregado")
        .filter(func.date(OrdenServicio.fecha_salida).between(d, h))
        .scalar()
    )

    facturas = Documento.query.filter(
        Documento.tipo == "factura", func.date(Documento.fecha).between(d, h)
    )
    num_facturas = facturas.count()
    total_facturado = (
        db.session.query(func.coalesce(func.sum(Documento.total), 0))
        .filter(Documento.tipo == "factura", func.date(Documento.fecha).between(d, h))
        .scalar()
    )
    total_pagado = (
        db.session.query(func.coalesce(func.sum(Documento.total), 0))
        .filter(
            Documento.tipo == "factura",
            Documento.estado == "pagada",
            func.date(Documento.fecha).between(d, h),
        )
        .scalar()
    )

    top_repuestos = (
        db.session.query(
            ItemRepuestoOrden.repuesto_id,
            func.sum(ItemRepuestoOrden.cantidad).label("cantidad"),
            func.sum(ItemRepuestoOrden.cantidad * ItemRepuestoOrden.precio_unitario).label("total"),
        )
        .join(OrdenServicio, OrdenServicio.id == ItemRepuestoOrden.orden_id)
        .filter(func.date(OrdenServicio.fecha_ingreso).between(d, h))
        .group_by(ItemRepuestoOrden.repuesto_id)
        .order_by(func.sum(ItemRepuestoOrden.cantidad).desc())
        .limit(10)
        .all()
    )
    # Resolver nombres de repuesto (algunos pueden haber sido borrados).
    from .models import Repuesto

    top = []
    for repuesto_id, cantidad, total in top_repuestos:
        rep = db.session.get(Repuesto, repuesto_id)
        top.append({"nombre": rep.nombre if rep else "(eliminado)", "cantidad": cantidad, "total": total})

    por_mecanico = (
        db.session.query(
            OrdenServicio.mecanico_id, func.count(OrdenServicio.id).label("ordenes")
        )
        .filter(OrdenServicio.estado == "entregado")
        .filter(func.date(OrdenServicio.fecha_salida).between(d, h))
        .group_by(OrdenServicio.mecanico_id)
        .order_by(func.count(OrdenServicio.id).desc())
        .all()
    )
    mecanicos = []
    for mecanico_id, ordenes in por_mecanico:
        mec = db.session.get(Usuario, mecanico_id) if mecanico_id else None
        mecanicos.append({"nombre": mec.nombre if mec else "Sin asignar", "ordenes": ordenes})

    return {
        "ordenes_ingresadas": ordenes_ingresadas,
        "ordenes_entregadas": ordenes_entregadas,
        "num_facturas": num_facturas,
        "total_facturado": total_facturado,
        "total_pagado": total_pagado,
        "top_repuestos": top,
        "por_mecanico": mecanicos,
    }


@reportes_bp.route("/")
@admin_required
def index():
    desde, hasta = _rango()
    datos = _datos(desde, hasta)
    return render_template("reportes.html", desde=desde, hasta=hasta, **datos)


@reportes_bp.route("/export")
@admin_required
def exportar():
    desde, hasta = _rango()
    d, h = desde.isoformat(), hasta.isoformat()

    facturas = (
        Documento.query.filter(
            Documento.tipo == "factura", func.date(Documento.fecha).between(d, h)
        )
        .order_by(Documento.fecha.asc())
        .all()
    )

    buffer = io.StringIO()
    buffer.write("﻿")  # BOM para que Excel reconozca UTF-8
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Numero", "Fecha", "Cliente", "Cedula", "Placa", "Subtotal", "IVA", "Total", "Estado"])
    for f in facturas:
        orden = f.orden
        writer.writerow([
            f.numero,
            f.fecha.strftime("%Y-%m-%d %H:%M"),
            orden.cliente.nombre if orden and orden.cliente else "",
            orden.cliente.cedula if orden and orden.cliente else "",
            orden.moto.placa if orden and orden.moto else "",
            f"{f.subtotal:.0f}",
            f"{f.iva:.0f}",
            f"{f.total:.0f}",
            f.estado,
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="reporte_{d}_a_{h}.csv"'},
    )
