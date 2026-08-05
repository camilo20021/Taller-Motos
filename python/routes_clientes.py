from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import Cliente, Moto
from .utils import mayus

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.route("/")
@login_required
def listar():
    q = request.args.get("q", "").strip()
    consulta = Cliente.query
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(
            db.or_(
                Cliente.nombre.ilike(patron),
                Cliente.cedula.ilike(patron),
                Cliente.celular.ilike(patron),
            )
        )
    clientes = consulta.order_by(Cliente.nombre.asc()).all()
    return render_template("clientes_listar.html", clientes=clientes, q=q)


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo():
    if request.method == "POST":
        cliente = Cliente(
            taller_id=current_user.taller_id,
            nombre=mayus(request.form["nombre"]),
            cedula=mayus(request.form["cedula"]),
            celular=request.form["celular"].strip(),
            correo=None,  # ya no se pide correo (avisos por WhatsApp)
            direccion=mayus(request.form.get("direccion")),
        )
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente registrado correctamente.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("clientes_form.html", cliente=None)


@clientes_bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":
        cliente.nombre = mayus(request.form["nombre"])
        cliente.cedula = mayus(request.form["cedula"])
        cliente.celular = request.form["celular"].strip()
        cliente.direccion = mayus(request.form.get("direccion"))
        db.session.commit()
        flash("Datos del cliente actualizados.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("clientes_form.html", cliente=cliente)


@clientes_bp.route("/<int:cliente_id>")
@login_required
def detalle(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("cliente_detalle.html", cliente=cliente)


@clientes_bp.route("/<int:cliente_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado.", "info")
    return redirect(url_for("clientes.listar"))


@clientes_bp.route("/<int:cliente_id>/motos/nueva", methods=["GET", "POST"])
@login_required
def nueva_moto(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":
        moto = Moto(
            cliente_id=cliente.id,
            placa=mayus(request.form["placa"]),
            marca=mayus(request.form["marca"]),
            modelo=mayus(request.form.get("modelo")),
            anio=request.form.get("anio") or None,
            color=mayus(request.form.get("color")),
            cilindraje=mayus(request.form.get("cilindraje")),
            kilometraje=request.form.get("kilometraje") or None,
        )
        db.session.add(moto)
        db.session.commit()
        flash("Moto registrada correctamente.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("motos_form.html", cliente=cliente, moto=None)


@clientes_bp.route("/motos/<int:moto_id>/editar", methods=["GET", "POST"])
@login_required
def editar_moto(moto_id):
    moto = Moto.query.get_or_404(moto_id)
    cliente = moto.cliente

    if request.method == "POST":
        moto.placa = mayus(request.form["placa"])
        moto.marca = mayus(request.form["marca"])
        moto.modelo = mayus(request.form.get("modelo"))
        moto.anio = request.form.get("anio") or None
        moto.color = mayus(request.form.get("color"))
        moto.cilindraje = mayus(request.form.get("cilindraje"))
        moto.kilometraje = request.form.get("kilometraje") or None
        db.session.commit()
        flash("Moto actualizada.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("motos_form.html", cliente=cliente, moto=moto)
