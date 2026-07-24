import json
import urllib.error
import urllib.request

from . import crypto_utils
from .models import Taller

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def _enviar(destinatario: str, asunto: str, cuerpo: str) -> tuple[bool, str]:
    """Envío "best-effort" vía la API de Brevo: si falla o no está
    configurado, nunca rompe la petición que lo llamó, solo devuelve un
    mensaje informativo.

    Se eligió Brevo (API HTTP con una sola clave) en vez de SMTP directo de
    Gmail porque Google restringe cada vez más las "contraseñas de
    aplicación" -- muchas cuentas (sobre todo con llaves de acceso) ya ni
    siquiera pueden generarlas.
    """
    if not destinatario:
        return False, "El cliente no tiene correo registrado, no se envió notificación."

    taller = Taller.query.first()
    if taller is None or not taller.correo_configurado:
        return False, "El correo del taller no está configurado, no se envió notificación."

    api_key = crypto_utils.descifrar(taller.brevo_api_key_cifrada)
    if not api_key:
        return False, "El correo del taller no está configurado correctamente, no se envió notificación."

    payload = {
        "sender": {
            "name": taller.mail_remitente_nombre or taller.nombre,
            "email": taller.mail_remitente_correo,
        },
        "to": [{"email": destinatario}],
        "subject": asunto,
        "textContent": cuerpo,
    }

    peticion = urllib.request.Request(
        BREVO_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(peticion, timeout=15):
            pass
        return True, f"Se notificó por correo a {destinatario}."
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="ignore")
        return False, f"No se pudo enviar el correo de notificación ({error.code}: {detalle})."
    except Exception as error:  # noqa: BLE001 - nunca debe romper la petición
        return False, f"No se pudo enviar el correo de notificación ({error})."


def enviar_moto_ingresada(orden) -> tuple[bool, str]:
    """Avisa por correo al cliente que su moto quedó ingresada al taller."""
    cliente = orden.cliente
    cuerpo = (
        f"Hola {cliente.nombre},\n\n"
        f"Confirmamos el ingreso de tu moto {orden.moto.marca} {orden.moto.modelo or ''} "
        f"(placa {orden.moto.placa}) a nuestro taller.\n\n"
        + (f"Problema reportado: {orden.problema_reportado}\n\n" if orden.problema_reportado else "")
        + f"Orden de servicio #{orden.id}. Te avisaremos cuando esté lista.\n\n"
        f"Gracias por confiar en nosotros."
    )
    return _enviar(cliente.correo, f"Recibimos tu moto {orden.moto.marca}", cuerpo)


def enviar_moto_lista(orden) -> tuple[bool, str]:
    """Avisa por correo al cliente que su moto ya está lista para recoger."""
    cliente = orden.cliente
    cuerpo = (
        f"Hola {cliente.nombre},\n\n"
        f"Tu moto {orden.moto.marca} {orden.moto.modelo or ''} (placa {orden.moto.placa}) "
        f"ya está lista para recoger.\n\n"
        f"Gracias por confiar en nosotros."
    )
    return _enviar(cliente.correo, f"Tu moto {orden.moto.marca} ya está lista", cuerpo)


def enviar_prueba(destinatario: str) -> tuple[bool, str]:
    """Correo de prueba para validar la configuración desde Ajustes → Correo."""
    return _enviar(
        destinatario,
        "Correo de prueba",
        "Este es un correo de prueba. Si lo recibiste, tu configuración de correo quedó bien.",
    )
