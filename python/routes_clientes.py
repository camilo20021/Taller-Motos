from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import Cliente, Moto

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
            nombre=request.form["nombre"].strip(),
            cedula=request.form["cedula"].strip(),
            celular=request.form["celular"].strip(),
            correo=request.form.get("correo", "").strip() or None,
            direccion=request.form.get("direccion", "").strip() or None,
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
        cliente.nombre = request.form["nombre"].strip()
        cliente.cedula = request.form["cedula"].strip()
        cliente.celular = request.form["celular"].strip()
        cliente.correo = request.form.get("correo", "").strip() or None
        cliente.direccion = request.form.get("direccion", "").strip() or None
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
            placa=request.form["placa"].strip().upper(),
            marca=request.form["marca"].strip(),
            modelo=request.form.get("modelo", "").strip() or None,
            anio=request.form.get("anio") or None,
            color=request.form.get("color", "").strip() or None,
            cilindraje=request.form.get("cilindraje", "").strip() or None,
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
        moto.placa = request.form["placa"].strip().upper()
        moto.marca = request.form["marca"].strip()
        moto.modelo = request.form.get("modelo", "").strip() or None
        moto.anio = request.form.get("anio") or None
        moto.color = request.form.get("color", "").strip() or None
        moto.cilindraje = request.form.get("cilindraje", "").strip() or None
        moto.kilometraje = request.form.get("kilometraje") or None
        db.session.commit()
        flash("Moto actualizada.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("motos_form.html", cliente=cliente, moto=moto)
