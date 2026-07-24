import os

from flask import Flask, redirect, request, send_from_directory, url_for

from .config import Config, APP_PRODUCTO
from .extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.setdefault("APP_PRODUCTO", APP_PRODUCTO)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Elige tu usuario para continuar."
    login_manager.login_message_category = "info"

    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.Usuario.query.get(int(user_id))

    from .routes_auth import auth_bp
    from .routes_dashboard import dashboard_bp
    from .routes_clientes import clientes_bp
    from .routes_ordenes import ordenes_bp
    from .routes_inventario import inventario_bp
    from .routes_documentos import documentos_bp
    from .routes_caja import caja_bp
    from .routes_usuarios import usuarios_bp
    from .routes_setup import setup_bp
    from .routes_respaldo import respaldo_bp
    from .routes_ajustes import ajustes_bp

    for blueprint in (
        auth_bp,
        dashboard_bp,
        clientes_bp,
        ordenes_bp,
        inventario_bp,
        documentos_bp,
        caja_bp,
        usuarios_bp,
        setup_bp,
        respaldo_bp,
        ajustes_bp,
    ):
        app.register_blueprint(blueprint)

    endpoints_publicos = {"setup.configurar", "css_files", "js_files"}

    @app.before_request
    def _requerir_configuracion_inicial():
        if request.endpoint in endpoints_publicos:
            return None
        if models.Taller.query.first() is None:
            return redirect(url_for("setup.configurar"))
        return None

    static_dir = os.path.join(app.root_path, "static")

    @app.route("/css/<path:filename>")
    def css_files(filename):
        return send_from_directory(os.path.join(static_dir, "css"), filename)

    @app.route("/js/<path:filename>")
    def js_files(filename):
        return send_from_directory(os.path.join(static_dir, "js"), filename)

    with app.app_context():
        db.create_all()
        _migrar_columnas_faltantes()
        if app.config["AUTO_SEED_INICIAL"]:
            _seed_inicial(app)

    return app


def _migrar_columnas_faltantes():
    """Agrega a las tablas ya existentes las columnas que se hayan sumado al
    modelo después de que esa base de datos se creó (ej. una instalación
    hecha antes de que existiera "Ajustes de correo"). db.create_all() solo
    crea tablas nuevas, nunca altera una tabla que ya existe -- por eso hace
    falta este paso para no dejar bases de datos viejas rotas."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    tablas_existentes = set(inspector.get_table_names())

    with db.engine.begin() as conexion:
        for tabla in db.metadata.sorted_tables:
            if tabla.name not in tablas_existentes:
                continue
            columnas_existentes = {c["name"] for c in inspector.get_columns(tabla.name)}
            for columna in tabla.columns:
                if columna.name in columnas_existentes:
                    continue
                tipo_sql = columna.type.compile(dialect=db.engine.dialect)
                conexion.execute(
                    text(f'ALTER TABLE "{tabla.name}" ADD COLUMN "{columna.name}" {tipo_sql}')
                )


def _seed_inicial(app):
    from . import crypto_utils
    from .models import Taller, Usuario

    if Taller.query.first() is not None:
        return

    taller = Taller(
        nombre=app.config["TALLER_NOMBRE"],
        nit=app.config["TALLER_NIT"],
        direccion=app.config["TALLER_DIRECCION"],
        telefono=app.config["TALLER_TELEFONO"],
    )

    # Conveniencia solo para desarrollo: si el .env trae una API key de
    # Brevo, se precarga para no tener que llenarla a mano en Ajustes.
    brevo_api_key = os.environ.get("BREVO_API_KEY")
    remitente_correo = os.environ.get("MAIL_REMITENTE_CORREO")
    if brevo_api_key and remitente_correo:
        taller.mail_remitente_correo = remitente_correo
        taller.mail_remitente_nombre = os.environ.get("MAIL_REMITENTE_NOMBRE", taller.nombre)

    db.session.add(taller)
    db.session.flush()

    if brevo_api_key and remitente_correo:
        taller.brevo_api_key_cifrada = crypto_utils.cifrar(brevo_api_key)

    admin = Usuario(
        taller_id=taller.id,
        nombre=app.config["ADMIN_NOMBRE"],
        rol="admin",
        activo=True,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
