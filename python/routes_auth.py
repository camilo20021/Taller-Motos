from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .models import Taller, Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def raiz():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    taller = Taller.query.first()
    taller_nombre = taller.nombre if taller else None

    if request.method == "POST":
        usuario = Usuario.query.get(request.form.get("usuario_id"))

        if usuario is None or not usuario.activo:
            flash("Selecciona un usuario válido de la lista.", "error")
            return redirect(url_for("auth.login"))

        if not usuario.es_admin:
            login_user(usuario)
            return redirect(url_for("dashboard.index"))

        # Los administradores sí necesitan contraseña, para que un mecánico
        # no pueda simplemente elegir "Administrador" de la lista.
        if "password" in request.form:
            if usuario.check_password(request.form.get("password", "")):
                login_user(usuario)
                return redirect(url_for("dashboard.index"))
            flash("Contraseña incorrecta.", "error")

        return render_template(
            "login_password.html", usuario=usuario, taller_nombre=taller_nombre
        )

    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre.asc()).all()
    return render_template("login.html", taller_nombre=taller_nombre, usuarios=usuarios)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
