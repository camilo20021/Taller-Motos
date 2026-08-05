from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import whatsapp
from .extensions import db
from .models import (
    ESTADOS_LAVADO,
    ESTADOS_ORDEN,
    Cliente,
    ItemRepuestoOrden,
    ItemServicioOrden,
    Moto,
    MovimientoInventario,
    OrdenServicio,
    Repuesto,
    Taller,
    Usuario,
)
from .utils import ahora_local, parse_float, parse_int

ordenes_bp = Blueprint("ordenes", __name__, url_prefix="/ordenes")

# Una orden entregada o cancelada está "cerrada": no se le pueden agregar ni
# quitar repuestos/servicios ni descontar más inventario.
ESTADOS_CERRADOS = ("entregado", "cancelado")


def _reintegrar_stock(orden, usuario_id):
    """Devuelve al inventario los repuestos usados en la orden (al cancelar)."""
    for item in orden.items_repuesto:
        item.repuesto.stock += item.cantidad
        db.session.add(
            MovimientoInventario(
                repuesto_id=item.repuesto_id,
                usuario_id=usuario_id,
                tipo="entrada",
                cantidad=item.cantidad,
            )
        )


@ordenes_bp.route("/")
@login_required
def listar():
    estado = request.args.get("estado", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    consulta = OrdenServicio.query
    if estado:
        consulta = consulta.filter_by(estado=estado)
    if q:
        patron = f"%{q}%"
        consulta = consulta.join(Moto, Moto.id == OrdenServicio.moto_id).join(
            Cliente, Cliente.id == OrdenServicio.cliente_id
        )
        filtros = [Moto.placa.ilike(patron), Cliente.nombre.ilike(patron)]
        if q.isdigit():
            filtros.append(OrdenServicio.id == int(q))
        consulta = consulta.filter(db.or_(*filtros))

    paginacion = consulta.order_by(OrdenServicio.fecha_ingreso.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "ordenes_listar.html",
        ordenes=paginacion.items,
        paginacion=paginacion,
        estado=estado,
        q=q,
        estados=ESTADOS_ORDEN,
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
            try:
                fecha_entrega = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
            except ValueError:
                fecha_entrega = None

        es_lavado = request.form.get("tipo") == "lavado"

        orden = OrdenServicio(
            cliente_id=cliente.id,
            moto_id=moto.id,
            mecanico_id=request.form.get("mecanico_id") or None,
            kilometraje_ingreso=parse_int(request.form.get("kilometraje_ingreso"), None),
            fecha_entrega_estimada=fecha_entrega,
            tipo="lavado" if es_lavado else "reparacion",
            problema_reportado=(None if es_lavado else request.form.get("problema_reportado", "").strip() or None),
            lavado_incluye=(request.form.get("incluye_lavado", "").strip() or None) if es_lavado else None,
            estado="recibida",
        )
        db.session.add(orden)
        db.session.flush()

        # En un lavado, el precio acordado se registra como servicio para que
        # entre en el total y en la factura igual que cualquier otro cobro.
        if es_lavado:
            precio = parse_float(request.form.get("precio_lavado"), 0)
            db.session.add(ItemServicioOrden(orden_id=orden.id, descripcion="Lavado de moto", precio=precio))

        db.session.commit()

        # Avisar al cliente por WhatsApp que su moto fue recibida.
        taller = Taller.query.first()
        whatsapp.abrir_whatsapp(orden.cliente.celular, whatsapp.mensaje_recibido(orden, taller))
        aviso = "Se abrió WhatsApp para avisar al cliente que se recibió la moto para lavado." if es_lavado \
            else "Se abrió WhatsApp para avisar al cliente que se recibió la moto."
        flash("Orden creada. " + aviso, "success")
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
        estados=ESTADOS_LAVADO if orden.es_lavado else ESTADOS_ORDEN,
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

    # No aceptar estados fuera del flujo definido (protege contra POST manipulados).
    if nuevo_estado not in ESTADOS_ORDEN:
        flash("Estado de orden inválido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    orden.estado = nuevo_estado
    orden.diagnostico = request.form.get("diagnostico", "").strip() or None
    orden.observaciones = request.form.get("observaciones", "").strip() or None

    if nuevo_estado == "entregado" and estado_anterior != "entregado":
        orden.fecha_salida = ahora_local()

    # Al cancelar una orden, se devuelven al inventario los repuestos usados
    # (solo la primera vez que pasa a "cancelado").
    if nuevo_estado == "cancelado" and estado_anterior != "cancelado":
        _reintegrar_stock(orden, current_user.id)

    db.session.commit()

    # Al marcar "Terminado", avisar al cliente por WhatsApp con observaciones y total.
    if nuevo_estado == "terminado" and estado_anterior != "terminado":
        taller = Taller.query.first()
        whatsapp.abrir_whatsapp(orden.cliente.celular, whatsapp.mensaje_terminado(orden, taller))
        flash("Se abrió WhatsApp para avisar al cliente que su moto está lista, con el valor a pagar.", "info")

    flash("Orden de servicio actualizada.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/whatsapp/<tipo>", methods=["POST"])
@login_required
def enviar_whatsapp(orden_id, tipo):
    """Reenvía manualmente el aviso de WhatsApp (recibido o terminado)."""
    orden = OrdenServicio.query.get_or_404(orden_id)
    taller = Taller.query.first()
    if tipo == "terminado":
        mensaje = whatsapp.mensaje_terminado(orden, taller)
    else:
        mensaje = whatsapp.mensaje_recibido(orden, taller)
    whatsapp.abrir_whatsapp(orden.cliente.celular, mensaje)
    flash("Se abrió WhatsApp con el mensaje listo para enviar al cliente.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/repuestos", methods=["POST"])
@login_required
def agregar_repuesto(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)

    if orden.estado in ESTADOS_CERRADOS:
        flash("La orden ya está cerrada; no se pueden agregar repuestos.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    repuesto = Repuesto.query.get_or_404(request.form.get("repuesto_id"))
    cantidad = parse_int(request.form.get("cantidad"), 0)

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


@ordenes_bp.route("/<int:orden_id>/repuestos/<int:item_id>/quitar", methods=["POST"])
@login_required
def quitar_repuesto(orden_id, item_id):
    orden = OrdenServicio.query.get_or_404(orden_id)

    if orden.estado in ESTADOS_CERRADOS:
        flash("La orden ya está cerrada; no se pueden quitar repuestos.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    item = ItemRepuestoOrden.query.filter_by(id=item_id, orden_id=orden.id).first_or_404()

    # Devolver la cantidad al inventario y dejar registro del movimiento.
    item.repuesto.stock += item.cantidad
    db.session.add(
        MovimientoInventario(
            repuesto_id=item.repuesto_id,
            usuario_id=current_user.id,
            tipo="entrada",
            cantidad=item.cantidad,
        )
    )
    nombre = item.repuesto.nombre
    db.session.delete(item)
    db.session.commit()
    flash(f"Se quitó {nombre} de la orden y volvió al inventario.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/servicios", methods=["POST"])
@login_required
def agregar_servicio(orden_id):
    orden = OrdenServicio.query.get_or_404(orden_id)

    if orden.estado in ESTADOS_CERRADOS:
        flash("La orden ya está cerrada; no se pueden agregar servicios.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    descripcion = request.form.get("descripcion", "").strip()
    precio = parse_float(request.form.get("precio"), -1)

    if not descripcion or precio < 0:
        flash("Descripción o precio inválido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    db.session.add(
        ItemServicioOrden(orden_id=orden.id, descripcion=descripcion, precio=precio)
    )
    db.session.commit()
    flash("Servicio agregado a la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/servicios/<int:item_id>/quitar", methods=["POST"])
@login_required
def quitar_servicio(orden_id, item_id):
    orden = OrdenServicio.query.get_or_404(orden_id)

    if orden.estado in ESTADOS_CERRADOS:
        flash("La orden ya está cerrada; no se pueden quitar servicios.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    item = ItemServicioOrden.query.filter_by(id=item_id, orden_id=orden.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Servicio quitado de la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))
