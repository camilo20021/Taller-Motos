"""Cifrado simétrico local para datos sensibles guardados en la base de datos
(por ahora, solo la contraseña de correo del taller).

La clave se deriva de SECRET_KEY, que es distinta en cada instalación (ver
desktop/main.py) -- así el archivo taller.db no expone la contraseña en
texto plano si alguien lo abre con un visor de SQLite.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet() -> Fernet:
    clave = current_app.config["SECRET_KEY"].encode("utf-8")
    digest = hashlib.sha256(clave).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode("utf-8")).decode("utf-8")


def descifrar(texto_cifrado: str) -> str | None:
    if not texto_cifrado:
        return None
    try:
        return _fernet().decrypt(texto_cifrado.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
