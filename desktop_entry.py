"""Punto de entrada para el ejecutable empaquetado (PyInstaller).

No pongas lógica aquí -- todo vive en desktop/main.py. Este archivo existe
porque PyInstaller ejecuta el script de entrada como "__main__", lo que rompe
los imports relativos ("from . import ...") dentro del paquete desktop/. Al
importar desktop.main como módulo (en vez de ejecutarlo directamente como
script), los imports relativos dentro de ese paquete funcionan con normalidad.
"""

from desktop.main import main

if __name__ == "__main__":
    main()
