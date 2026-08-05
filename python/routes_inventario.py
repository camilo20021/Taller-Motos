from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .decorators import admin_required
from .extensions import db
from .models import MovimientoInventario, Repuesto

inventario_bp = Blueprint("inventario", __name__, url_prefix="/inventario")


@inventario_bp.route("/")
@admin_required
def listar():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    consulta = Repuesto.query
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(
            db.or_(Repuesto.nombre.ilike(patron), Repuesto.codigo.ilike(patron))
        )
    paginacion = consulta.order_by(Repuesto.nombre.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "inventario_listar.html", repuestos=paginacion.items, paginacion=paginacion, q=q
    )


@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo():
    if request.method == "POST":
        repuesto = Repuesto(
            taller_id=current_user.taller_id,
            codigo=request.form.get("codigo", "").strip() or None,
            nombre=request.form["nombre"].strip(),
            categoria=request.form.get("categoria", "").strip() or None,
            proveedor=request.form.get("proveedor", "").strip() or None,
            stock=int(request.form.get("stock") or 0),
            stock_minimo=int(request.form.get("stock_minimo") or 0),
            precio_compra=float(request.form.get("precio_compra") or 0),
            precio_venta=float(request.form.get("precio_venta") or 0),
        )
        db.session.add(repuesto)
        db.session.commit()
        flash("Repuesto agregado al inventario.", "success")
        return redirect(url_for("inventario.listar"))

    return render_template("inventario_form.html", repuesto=None)


@inventario_bp.route("/<int:repuesto_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(repuesto_id):
    repuesto = Repuesto.query.get_or_404(repuesto_id)

    if request.method == "POST":
        repuesto.codigo = request.form.get("codigo", "").strip() or None
        repuesto.nombre = request.form["nombre"].strip()
        repuesto.categoria = request.form.get("categoria", "").strip() or None
        repuesto.proveedor = request.form.get("proveedor", "").strip() or None
        repuesto.stock_minimo = int(request.form.get("stock_minimo") or 0)
        repuesto.precio_compra = float(request.form.get("precio_compra") or 0)
        repuesto.precio_venta = float(request.form.get("precio_venta") or 0)
        db.session.commit()
        flash("Repuesto actualizado.", "success")
        return redirect(url_for("inventario.listar"))

    return render_template("inventario_form.html", repuesto=repuesto)


@inventario_bp.route("/<int:repuesto_id>/movimiento", methods=["POST"])
@admin_required
def registrar_movimiento(repuesto_id):
    repuesto = Repuesto.query.get_or_404(repuesto_id)
    tipo = request.form.get("tipo")
    cantidad = int(request.form.get("cantidad", 0))

    if cantidad <= 0 or tipo not in ("entrada", "salida"):
        flash("Movimiento inválido.", "error")
        return redirect(url_for("inventario.listar"))

    if tipo == "salida" and cantidad > repuesto.stock:
        flash(f"No hay stock suficiente de {repuesto.nombre}.", "error")
        return redirect(url_for("inventario.listar"))

    repuesto.stock += cantidad if tipo == "entrada" else -cantidad
    db.session.add(
        MovimientoInventario(
            repuesto_id=repuesto.id,
            usuario_id=current_user.id,
            tipo=tipo,
            cantidad=cantidad,
        )
    )
    db.session.commit()
    flash(f"Movimiento de {tipo} registrado para {repuesto.nombre}.", "success")
    return redirect(url_for("inventario.listar"))
