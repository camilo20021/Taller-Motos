"""Utilidades compartidas: parseo seguro de formularios y hora local.

Se centraliza aquí para no repetir try/except en cada ruta y para que las
fechas se guarden en hora de Colombia (no UTC), que es lo que el usuario ve.
"""

from datetime import datetime, timedelta, timezone

# Colombia siempre está en UTC-5 (no tiene horario de verano), así que se usa
# un desfase fijo en vez de zoneinfo/tzdata para no depender de paquetes extra
# ni de la configuración del sistema.
_TZ_COLOMBIA = timezone(timedelta(hours=-5))


def ahora_local() -> datetime:
    """Fecha y hora actual de Colombia como datetime ingenuo (sin tzinfo),
    para ser consistente con el resto de columnas del modelo."""
    return datetime.now(_TZ_COLOMBIA).replace(tzinfo=None)


def parse_int(valor, defecto=0) -> int:
    """Convierte a entero sin reventar; devuelve `defecto` si no es válido."""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError, AttributeError):
        return defecto


def parse_float(valor, defecto=0.0) -> float:
    """Convierte a número decimal sin reventar; acepta coma o punto decimal."""
    try:
        return float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        return defecto


def mayus(valor, defecto=None):
    """Normaliza texto a MAYÚSCULAS y sin espacios sobrantes. Devuelve
    `defecto` si queda vacío. Se usa para que los datos de clientes/motos
    queden uniformes y organizados."""
    v = (valor or "").strip().upper()
    return v or defecto
