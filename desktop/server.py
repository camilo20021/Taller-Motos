"""Arranca el backend Flask en un hilo, sirviendo en un puerto local libre."""

import socket
import threading

from waitress import serve


def puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def iniciar_servidor(app, puerto: int) -> threading.Thread:
    hilo = threading.Thread(
        target=serve,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": puerto},
        daemon=True,
    )
    hilo.start()
    return hilo
