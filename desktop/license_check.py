"""Validación offline de la licencia de uso (sin necesitar servidor).

El archivo de licencia (.lic) lo genera el vendedor con
tools/generate_license.py usando una clave privada Ed25519 que nunca se
distribuye. Aquí solo se VERIFICA la firma con la clave pública embebida en
desktop/license_public_key.py — nunca se puede generar una licencia válida
sin la clave privada.
"""

import base64
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import appdata
from .license_public_key import PUBLIC_KEY_B64

DIAS_GRACIA = 30  # 1 mes de prueba antes de exigir una licencia comprada.
NOMBRE_ARCHIVO_LICENCIA = "activation.lic"
PRODUCTO_ESPERADO = "taller-motos-desktop"


@dataclass
class EstadoLicencia:
    valida: bool
    en_gracia: bool
    taller: str | None
    dias_restantes_gracia: int | None
    mensaje: str


def _clave_publica() -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))


def _ruta_licencia() -> Path:
    return appdata.license_dir() / NOMBRE_ARCHIVO_LICENCIA


def _leer_payload_valido(contenido: str) -> dict | None:
    try:
        payload_b64, firma_b64 = contenido.strip().split(".")
        payload_bytes = base64.b64decode(payload_b64)
        firma = base64.b64decode(firma_b64)
        _clave_publica().verify(firma, payload_bytes)
        payload = json.loads(payload_bytes)
    except (ValueError, InvalidSignature, json.JSONDecodeError):
        return None

    if payload.get("product") != PRODUCTO_ESPERADO:
        return None
    return payload


def _dias_desde_primer_arranque() -> int:
    marca = appdata.marca_primer_arranque_path()
    ahora = datetime.utcnow()
    if not marca.exists():
        marca.write_text(ahora.isoformat(), encoding="utf-8")
        return 0
    try:
        primera_vez = datetime.fromisoformat(marca.read_text(encoding="utf-8").strip())
    except ValueError:
        primera_vez = ahora
    return (ahora - primera_vez).days


def verificar() -> EstadoLicencia:
    ruta = _ruta_licencia()
    dias_transcurridos = _dias_desde_primer_arranque()
    dias_restantes_gracia = max(DIAS_GRACIA - dias_transcurridos, 0)

    if ruta.exists():
        payload = _leer_payload_valido(ruta.read_text(encoding="utf-8"))
        if payload is None:
            return EstadoLicencia(
                valida=False,
                en_gracia=dias_restantes_gracia > 0,
                taller=None,
                dias_restantes_gracia=dias_restantes_gracia,
                mensaje="El archivo de licencia no es válido.",
            )

        vencida = date.fromisoformat(payload["expiry"]) < date.today()
        if not vencida:
            return EstadoLicencia(
                valida=True,
                en_gracia=False,
                taller=payload.get("taller"),
                dias_restantes_gracia=None,
                mensaje=f"Licenciado a: {payload.get('taller')}",
            )
        return EstadoLicencia(
            valida=False,
            en_gracia=dias_restantes_gracia > 0,
            taller=payload.get("taller"),
            dias_restantes_gracia=dias_restantes_gracia,
            mensaje="La licencia expiró. Contacta al vendedor para renovarla.",
        )

    if dias_restantes_gracia > 0:
        return EstadoLicencia(
            valida=False,
            en_gracia=True,
            taller=None,
            dias_restantes_gracia=dias_restantes_gracia,
            mensaje=f"Versión de prueba: quedan {dias_restantes_gracia} día(s) antes de activar.",
        )

    return EstadoLicencia(
        valida=False,
        en_gracia=False,
        taller=None,
        dias_restantes_gracia=0,
        mensaje="Este programa necesita una licencia para seguir usándose.",
    )


def activar_licencia(ruta_archivo_elegido: str) -> tuple[bool, str]:
    origen = Path(ruta_archivo_elegido)
    if not origen.exists():
        return False, "El archivo seleccionado no existe."

    contenido = origen.read_text(encoding="utf-8")
    payload = _leer_payload_valido(contenido)
    if payload is None:
        return False, "El archivo de licencia no es válido o fue alterado."

    if date.fromisoformat(payload["expiry"]) < date.today():
        return False, f"Esta licencia venció el {payload['expiry']}. Pide una nueva."

    _ruta_licencia().write_text(contenido, encoding="utf-8")
    return True, f"Licencia activada para {payload.get('taller')}."
