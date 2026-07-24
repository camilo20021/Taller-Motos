"""Generador de licencias — SOLO para el vendedor, nunca se distribuye.

Uso:
    python tools/generate_license.py

Pide los datos del taller comprador y firma un archivo <taller>-activation.lic
con la clave privada en tools/private_key.pem (nunca subir ese .pem a git ni
enviarlo al cliente — ver .gitignore). El cliente solo recibe el .lic
resultante y lo importa desde la pantalla de activación de la aplicación.

Si tools/private_key.pem no existe todavía, este script genera un par de
claves nuevo la primera vez que se ejecuta.
"""

import base64
import json
import re
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CLAVE_PRIVADA = Path(__file__).resolve().parent / "private_key.pem"
PRODUCTO = "taller-motos-desktop"


def _cargar_o_crear_clave_privada() -> Ed25519PrivateKey:
    if RUTA_CLAVE_PRIVADA.exists():
        return serialization.load_pem_private_key(
            RUTA_CLAVE_PRIVADA.read_bytes(), password=None
        )

    print("No existe una clave privada todavía, generando una nueva...")
    clave = Ed25519PrivateKey.generate()
    pem = clave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    RUTA_CLAVE_PRIVADA.write_bytes(pem)

    publica = clave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    publica_b64 = base64.b64encode(publica).decode()
    print(f"\nIMPORTANTE: actualiza desktop/license_public_key.py con esta clave pública")
    print(f"y vuelve a compilar la aplicación antes de vender licencias:\n")
    print(f'  PUBLIC_KEY_B64 = "{publica_b64}"\n')

    return clave


def _slug(texto: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto.strip().lower()).strip("-")
    return slug or "taller"


def main():
    clave_privada = _cargar_o_crear_clave_privada()

    print("=== Generar licencia para un nuevo taller ===")
    taller = input("Nombre del taller: ").strip()
    dias = input("Días de validez [365]: ").strip() or "365"
    cupos = input("Cupos / equipos autorizados [1]: ").strip() or "1"

    payload = {
        "taller": taller,
        "license_id": f"TM-{uuid.uuid4().hex[:12].upper()}",
        "issued": date.today().isoformat(),
        "expiry": (date.today() + timedelta(days=int(dias))).isoformat(),
        "seats": int(cupos),
        "product": PRODUCTO,
    }

    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    firma = clave_privada.sign(payload_bytes)

    contenido = f"{base64.b64encode(payload_bytes).decode()}.{base64.b64encode(firma).decode()}"

    destino = RAIZ / f"{_slug(taller)}-activation.lic"
    destino.write_text(contenido, encoding="utf-8")

    print(f"\nLicencia generada: {destino}")
    print(f"Vence: {payload['expiry']}")
    print("Envíasela al cliente para que la importe desde la pantalla de activación.")


if __name__ == "__main__":
    sys.exit(main())
