from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user

from .extensions import db
from .models import Taller, Usuario

setup_bp = Blueprint("setup", __name__)


@setup_bp.route("/setup", methods=["GET", "POST"])
def configurar():
    if Taller.query.first() is not None:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nombre_admin = request.form.get("admin_nombre", "").strip()
        nombre_taller = request.form.get("taller_nombre", "").strip()
        celular_taller = request.form.get("taller_telefono", "").strip()
        password = request.form.get("admin_password", "")
        confirmar = request.form.get("admin_password_confirmar", "")

        if not nombre_taller or not nombre_admin:
            flash("Completa el nombre del taller y tu nombre para continuar.", "error")
        elif not celular_taller:
            flash("Indica el celular del taller: se usa para enviar los avisos por WhatsApp.", "error")
        elif len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
        elif password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
        else:
            taller = Taller(
                nombre=nombre_taller,
                nit=request.form.get("taller_nit", "").strip() or None,
                direccion=request.form.get("taller_direccion", "").strip() or None,
                telefono=celular_taller,
            )
            db.session.add(taller)
            db.session.flush()

            admin = Usuario(
                taller_id=taller.id,
                nombre=nombre_admin,
                rol="admin",
                activo=True,
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()

            login_user(admin)
            flash(f"¡Listo! {taller.nombre} quedó configurado.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("setup.html")
