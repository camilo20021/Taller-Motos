"""Arranca el backend Flask en un hilo.

Se sirve en 0.0.0.0 (todas las interfaces) y en un puerto FIJO para que las
tablets del taller puedan conectarse por Wi-Fi a una dirección estable
(http://IP-DEL-EQUIPO:5000), no solo desde la misma máquina.
"""

import socket
import threading

from waitress import serve

PUERTO_PREFERIDO = 5000


def _puerto_disponible(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", puerto))
            return True
        except OSError:
            return False


def elegir_puerto() -> int:
    """Puerto fijo (5000) para una dirección estable; si está ocupado, uno libre."""
    if _puerto_disponible(PUERTO_PREFERIDO):
        return PUERTO_PREFERIDO
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


# Alias por compatibilidad con llamadas antiguas.
def puerto_libre() -> int:
    return elegir_puerto()


def ip_local() -> str:
    """IP del equipo en la red local, para armar la URL que usan las tablets."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # No envía datos; solo hace que el SO elija la interfaz de salida.
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def iniciar_servidor(app, puerto: int) -> threading.Thread:
    hilo = threading.Thread(
        target=serve,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": puerto, "threads": 8},
        daemon=True,
    )
    hilo.start()
    return hilo
