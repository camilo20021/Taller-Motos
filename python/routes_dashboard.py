from flask import Blueprint, render_template
from flask_login import login_required

from .models import Cliente, Moto, OrdenServicio, Repuesto

dashboard_bp = Blueprint("dashboard", __name__)

ESTADOS_ACTIVOS = ["recibida", "diagnostico", "en_reparacion", "esperando_repuesto"]


@dashboard_bp.route("/dashboard")
@login_required
def index():
    total_clientes = Cliente.query.count()
    total_motos = Moto.query.count()
    ordenes_activas = OrdenServicio.query.filter(
        OrdenServicio.estado.in_(ESTADOS_ACTIVOS)
    ).count()
    ultimas_ordenes = (
        OrdenServicio.query.order_by(OrdenServicio.fecha_ingreso.desc()).limit(8).all()
    )
    repuestos_bajos = [r for r in Repuesto.query.all() if r.stock_bajo]

    return render_template(
        "dashboard.html",
        total_clientes=total_clientes,
        total_motos=total_motos,
        ordenes_activas=ordenes_activas,
        ultimas_ordenes=ultimas_ordenes,
        repuestos_bajos=repuestos_bajos,
    )
