"""Evita que el programa se abra dos veces al mismo tiempo.

Se implementa reservando un puerto TCP fijo en localhost como "mutex": si el
bind falla, ya hay otra instancia corriendo. No depende de librerías extra de
Windows (pywin32) y es suficiente para un programa de un solo usuario local.
"""

import socket

_PUERTO_CANDADO = 47811

# Se mantiene una referencia global para que el socket no se cierre por el
# recolector de basura mientras la aplicación sigue abierta.
_socket_candado: socket.socket | None = None


def ya_hay_una_instancia() -> bool:
    global _socket_candado
    _socket_candado = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _socket_candado.bind(("127.0.0.1", _PUERTO_CANDADO))
        _socket_candado.listen(1)
        return False
    except OSError:
        return True
