from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .email_utils import enviar_moto_ingresada, enviar_moto_lista
from .extensions import db
from .models import (
    ESTADOS_ORDEN,
    Cliente,
    ItemRepuestoOrden,
    ItemServicioOrden,
    MovimientoInventario,
    OrdenServicio,
    Repuesto,
    Usuario,
)

ordenes_bp = Blueprint("ordenes", __name__, url_prefix="/ordenes")


@ordenes_bp.route("/")
@login_required
def listar():
    estado = request.args.get("estado", "")
    consulta = OrdenServicio.query
    if estado:
        consulta = consulta.filter_by(estado=estado)
    ordenes = consulta.order_by(OrdenServicio.fecha_ingreso.desc()).all()
    return render_template(
        "ordenes_listar.html", ordenes=ordenes, estado=estado, estados=ESTADOS_ORDEN
    )


@ordenes_bp.route("/buscar-cliente")
@login_required
def buscar_cliente():
    cedula = request.args.get("cedula", "").strip()
    cliente = Cliente.query.filter_by(cedula=cedula).first()
    if cliente is None:
        flash("No se encontró ningún cliente con esa cédula.", "error")
        return redirect(url_for("ordenes.nueva"))
    return redirect(url_for("ordenes.nueva", cliente_id=cliente.id))


@ordenes_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    cliente_id = request.args.get("cliente_id") or request.form.get("cliente_id")
    cliente = Cliente.query.get(cliente_id) if cliente_id else None

    if request.method == "POST" and cliente is not None:
        moto_id = request.form.get("moto_id")
        moto = next((m for m in cliente.motos if str(m.id) == moto_id), None)
        if moto is None:
            flash("Selecciona una moto válida de este cliente.", "error")
            return redirect(url_for("ordenes.nueva", cliente_id=cliente.id))

        fecha_entrega = request.form.get("fecha_entrega_estimada") or None
        if fecha_entrega:
            fecha_entrega = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()

        orden = OrdenServicio(
            cliente_id=cliente.id,
            moto_id=moto.id,
            mecanico_id=request.form.get("mecanico_id") or None,
            kilometraje_ingreso=request.form.get("kilometraje_ingreso") or None,
            fecha_entrega_estimada=fecha_entrega,
            problema_reportado=request.form.get("problema_reportado", "").strip() or None,
            estado="recibida",
        )
        db.session.add(orden)
        db.session.commit()

        _enviado, mensaje_correo = enviar_moto_ingresada(orden)
        flash("Orden de servicio creada. Se registró el ingreso de la moto.", "success")
        flash(mensaje_correo, "info")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    mecanicos = Usuario.query.filter_by(rol="mecanico", activo=True).all()
    return render_template("orden_form.html", cliente=cliente, mecanicos=mecanicos)


@ordenes_bp.route("/<int:orden_id>")
@login_required
def detalle(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)
    repuestos_disponibles = Repuesto.query.filter(Repuesto.stock > 0).order_by(
        Repuesto.nombre.asc()
    ).all()
    return render_template(
        "orden_detalle.html",
        orden=orden,
        estados=ESTADOS_ORDEN,
        repuestos_disponibles=repuestos_disponibles,
        subtotal_repuestos=orden.subtotal_repuestos,
        subtotal_servicios=orden.subtotal_servicios,
        subtotal_total=orden.subtotal_total,
    )


@ordenes_bp.route("/<int:orden_id>/estado", methods=["POST"])
@login_required
def cambiar_estado(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)
    estado_anterior = orden.estado
    nuevo_estado = request.form.get("estado", orden.estado)

    orden.estado = nuevo_estado
    orden.diagnostico = request.form.get("diagnostico", "").strip() or None
    orden.observaciones = request.form.get("observaciones", "").strip() or None

    if nuevo_estado == "entregado" and estado_anterior != "entregado":
        orden.fecha_salida = datetime.utcnow()

    db.session.commit()

    if nuevo_estado == "terminado" and estado_anterior != "terminado":
        _enviado, mensaje = enviar_moto_lista(orden)
        flash(mensaje, "info")

    flash("Orden de servicio actualizada.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/repuestos", methods=["POST"])
@login_required
def agregar_repuesto(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)
    repuesto = Repuesto.query.get_or_404(request.form.get("repuesto_id"))
    cantidad = int(request.form.get("cantidad", 1))

    if cantidad <= 0:
        flash("La cantidad debe ser mayor a cero.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    if cantidad > repuesto.stock:
        flash(f"No hay stock suficiente de {repuesto.nombre} (disponible: {repuesto.stock}).", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    item = ItemRepuestoOrden(
        orden_id=orden.id,
        repuesto_id=repuesto.id,
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
    )
    repuesto.stock -= cantidad
    db.session.add(item)
    db.session.add(
        MovimientoInventario(
            repuesto_id=repuesto.id,
            usuario_id=current_user.id,
            tipo="salida",
            cantidad=cantidad,
        )
    )
    db.session.commit()
    flash(f"Se agregó {repuesto.nombre} a la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/servicios", methods=["POST"])
@login_required
def agregar_servicio(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)
    descripcion = request.form.get("descripcion", "").strip()
    precio = float(request.form.get("precio", 0))

    if not descripcion or precio < 0:
        flash("Descripción o precio inválido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    db.session.add(
        ItemServicioOrden(orden_id=orden.id, descripcion=descripcion, precio=precio)
    )
    db.session.commit()
    flash("Servicio agregado a la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))
