from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .decorators import admin_required
from .extensions import db
from .models import Usuario

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuarios_bp.route("/")
@admin_required
def listar():
    usuarios = Usuario.query.order_by(Usuario.nombre.asc()).all()
    return render_template("usuarios_listar.html", usuarios=usuarios)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo():
    if request.method == "POST":
        rol = "admin" if request.form.get("rol") == "admin" else "mecanico"
        nombre = request.form["nombre"].strip()

        if rol == "admin":
            password = request.form.get("password", "")
            confirmar = request.form.get("password_confirmar", "")
            if len(password) < 6:
                flash("La contraseña del administrador debe tener al menos 6 caracteres.", "error")
                return render_template("usuario_form.html")
            if password != confirmar:
                flash("Las contraseñas no coinciden.", "error")
                return render_template("usuario_form.html")

        usuario = Usuario(
            taller_id=current_user.taller_id,
            nombre=nombre,
            rol=rol,
            activo=True,
        )
        if rol == "admin":
            usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()
        flash(f"{usuario.nombre} ya puede usar el programa.", "success")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuario_form.html")


@usuarios_bp.route("/<int:usuario_id>/password", methods=["GET", "POST"])
@admin_required
def cambiar_password(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if not usuario.es_admin:
        flash("Solo las cuentas de administrador usan contraseña.", "error")
        return redirect(url_for("usuarios.listar"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirmar = request.form.get("password_confirmar", "")
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
        elif password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
        else:
            usuario.set_password(password)
            db.session.commit()
            flash(f"Se cambió la contraseña de {usuario.nombre}.", "success")
            return redirect(url_for("usuarios.listar"))

    return render_template("usuario_password_form.html", usuario=usuario)


@usuarios_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@admin_required
def cambiar_estado(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.id == current_user.id:
        flash("No puedes cambiar el estado de tu propia cuenta.", "error")
        return redirect(url_for("usuarios.listar"))

    usuario.activo = not usuario.activo
    db.session.commit()
    flash(f"Cuenta de {usuario.nombre} {'activada' if usuario.activo else 'desactivada'}.", "success")
    return redirect(url_for("usuarios.listar"))
