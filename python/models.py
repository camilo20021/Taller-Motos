from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

ESTADOS_ORDEN = [
    "recibida",
    "diagnostico",
    "en_reparacion",
    "esperando_repuesto",
    "terminado",
    "entregado",
    "cancelado",
]

IVA_PORCENTAJE = 0.19


def _label(valor: str) -> str:
    return valor.replace("_", " ").capitalize()


class Taller(db.Model):
    __tablename__ = "talleres"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    nit = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(50))

    # Configuración de correo propia de este taller (para el aviso "moto
    # lista"/"moto ingresada"), enviado vía la API de Brevo -- se eligió en
    # vez de SMTP directo de Gmail porque Google restringe cada vez más las
    # "contraseñas de aplicación" en cuentas nuevas o con llaves de acceso.
    # La API key se guarda cifrada, nunca en texto plano -- ver crypto_utils.py.
    brevo_api_key_cifrada = db.Column(db.Text)
    mail_remitente_nombre = db.Column(db.String(150))
    mail_remitente_correo = db.Column(db.String(150))

    usuarios = db.relationship("Usuario", back_populates="taller", lazy=True)
    clientes = db.relationship("Cliente", back_populates="taller", lazy=True)
    repuestos = db.relationship("Repuesto", back_populates="taller", lazy=True)

    @property
    def correo_configurado(self) -> bool:
        return bool(self.brevo_api_key_cifrada and self.mail_remitente_correo)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="mecanico")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    # Solo los administradores usan contraseña -- el mecánico entra solo
    # eligiendo su nombre. Por eso es nullable: un mecánico no tiene una.
    password_hash = db.Column(db.String(255), nullable=True)

    taller = db.relationship("Taller", back_populates="usuarios")

    @property
    def es_admin(self) -> bool:
        return self.rol == "admin"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Flask-Login desactiva la sesión si la cuenta fue inhabilitada.
        return str(self.id) if self.activo else None


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(30), nullable=False)
    celular = db.Column(db.String(30), nullable=False)
    correo = db.Column(db.String(150))
    direccion = db.Column(db.String(200))

    taller = db.relationship("Taller", back_populates="clientes")
    motos = db.relationship(
        "Moto", back_populates="cliente", lazy=True, cascade="all, delete-orphan"
    )


class Moto(db.Model):
    __tablename__ = "motos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    marca = db.Column(db.String(80), nullable=False)
    modelo = db.Column(db.String(80))
    anio = db.Column(db.Integer)
    color = db.Column(db.String(50))
    cilindraje = db.Column(db.String(30))
    kilometraje = db.Column(db.Integer)

    cliente = db.relationship("Cliente", back_populates="motos")


class OrdenServicio(db.Model):
    __tablename__ = "ordenes_servicio"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    moto_id = db.Column(db.Integer, db.ForeignKey("motos.id"), nullable=False)
    mecanico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    fecha_ingreso = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_entrega_estimada = db.Column(db.Date)
    fecha_salida = db.Column(db.DateTime)
    kilometraje_ingreso = db.Column(db.Integer)

    problema_reportado = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(30), nullable=False, default="recibida")

    cliente = db.relationship("Cliente")
    moto = db.relationship("Moto")
    mecanico = db.relationship("Usuario")

    items_repuesto = db.relationship(
        "ItemRepuestoOrden", back_populates="orden", cascade="all, delete-orphan"
    )
    items_servicio = db.relationship(
        "ItemServicioOrden", back_populates="orden", cascade="all, delete-orphan"
    )

    @property
    def estado_label(self) -> str:
        return _label(self.estado)

    @property
    def subtotal_repuestos(self):
        return sum(item.subtotal for item in self.items_repuesto)

    @property
    def subtotal_servicios(self):
        return sum(item.precio for item in self.items_servicio)

    @property
    def subtotal_total(self):
        return self.subtotal_repuestos + self.subtotal_servicios


class ItemRepuestoOrden(db.Model):
    __tablename__ = "items_repuesto_orden"

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    repuesto_id = db.Column(db.Integer, db.ForeignKey("repuestos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    orden = db.relationship("OrdenServicio", back_populates="items_repuesto")
    repuesto = db.relationship("Repuesto")

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class ItemServicioOrden(db.Model):
    __tablename__ = "items_servicio_orden"

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    precio = db.Column(db.Float, nullable=False)

    orden = db.relationship("OrdenServicio", back_populates="items_servicio")


class Repuesto(db.Model):
    __tablename__ = "repuestos"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    codigo = db.Column(db.String(50))
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(80))
    proveedor = db.Column(db.String(150))
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    precio_compra = db.Column(db.Float, nullable=False, default=0)
    precio_venta = db.Column(db.Float, nullable=False, default=0)

    taller = db.relationship("Taller", back_populates="repuestos")

    @property
    def stock_bajo(self) -> bool:
        return self.stock <= self.stock_minimo


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"

    id = db.Column(db.Integer, primary_key=True)
    repuesto_id = db.Column(db.Integer, db.ForeignKey("repuestos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    tipo = db.Column(db.String(10), nullable=False)  # entrada | salida
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    repuesto = db.relationship("Repuesto")
    usuario = db.relationship("Usuario")


class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    cierre_caja_id = db.Column(db.Integer, db.ForeignKey("cierres_caja.id"))
    numero = db.Column(db.String(30), nullable=False, unique=True)
    tipo = db.Column(db.String(20), nullable=False)  # cotizacion | factura
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    subtotal = db.Column(db.Float, nullable=False)
    iva = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")  # pendiente | pagada

    orden = db.relationship("OrdenServicio")


class CierreCaja(db.Model):
    __tablename__ = "cierres_caja"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    abierto_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    cerrado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    fecha_apertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime)
    monto_inicial = db.Column(db.Float, nullable=False, default=0)
    monto_contado = db.Column(db.Float)
    observaciones = db.Column(db.Text)

    abierto_por = db.relationship("Usuario", foreign_keys=[abierto_por_id])
    cerrado_por = db.relationship("Usuario", foreign_keys=[cerrado_por_id])
    documentos = db.relationship("Documento", backref="cierre_caja", lazy=True)

    @property
    def total_ventas(self):
        return sum(d.total for d in self.documentos if d.estado == "pagada")

    @property
    def monto_esperado(self):
        return self.monto_inicial + self.total_ventas

    @property
    def diferencia(self):
        if self.monto_contado is None:
            return None
        return self.monto_contado - self.monto_esperado
