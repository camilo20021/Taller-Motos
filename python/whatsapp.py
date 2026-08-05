"""Notificaciones al cliente por WhatsApp (modo semi-automático, gratis).

En vez de enviar el mensaje solo (que exigiría la API de pago de WhatsApp
Business), se abre WhatsApp — el que ya esté abierto en el PC, Web o
Escritorio — con el mensaje YA ESCRITO al número del cliente. El taller solo
da clic en "Enviar". Sin costos ni configuración.
"""

import os
import urllib.parse
import webbrowser


def _solo_digitos(valor) -> str:
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def _numero_internacional(celular: str) -> str:
    """Agrega el indicativo de Colombia (57) a celulares de 10 dígitos."""
    n = _solo_digitos(celular)
    if len(n) == 10:
        return "57" + n
    return n


def link_whatsapp(celular: str, mensaje: str) -> str:
    return f"https://wa.me/{_numero_internacional(celular)}?text={urllib.parse.quote(mensaje)}"


def abrir_whatsapp(celular: str, mensaje: str) -> str:
    """Abre WhatsApp con el mensaje listo. Devuelve el enlace usado.
    Si TALLER_NO_BROWSER=1 (por ej. en pruebas) no abre nada."""
    url = link_whatsapp(celular, mensaje)
    if os.environ.get("TALLER_NO_BROWSER") != "1":
        try:
            webbrowser.open(url)
        except Exception:  # nunca debe romper la petición
            pass
    return url


def total_a_pagar(orden, taller) -> float:
    iva = taller.iva_porcentaje if taller and taller.iva_porcentaje is not None else 0.19
    return round(orden.subtotal_total * (1 + iva))


def mensaje_recibido(orden, taller) -> str:
    """Aviso al cliente de que su moto quedó recibida (reparación o lavado)."""
    m = orden.moto
    es_lavado = getattr(orden, "es_lavado", False)
    encabezado = "recibimos tu moto para lavado en" if es_lavado else "recibimos tu moto en"
    lineas = [
        f"Hola {orden.cliente.nombre}, {encabezado} {taller.nombre}.",
        f"Moto: {m.marca} {m.modelo or ''}".strip() + f" · Placa: {m.placa}",
    ]
    if es_lavado:
        if orden.lavado_incluye:
            lineas.append(f"El lavado incluye: {orden.lavado_incluye}")
        lineas.append(f"Valor acordado: ${total_a_pagar(orden, taller):,.0f}")
    else:
        detalles = []
        if m.anio:
            detalles.append(f"Año {m.anio}")
        if m.color:
            detalles.append(f"Color {m.color}")
        if m.cilindraje:
            detalles.append(str(m.cilindraje))
        if orden.kilometraje_ingreso:
            detalles.append(f"{orden.kilometraje_ingreso} km")
        if detalles:
            lineas.append(" · ".join(detalles))
        if orden.problema_reportado:
            lineas.append(f"Problema reportado: {orden.problema_reportado}")
    lineas.append(f"Orden de servicio: #{orden.id}")
    lineas.append("Te avisaremos cuando esté lista.")
    if taller.telefono:
        lineas.append(f"Contacto: {taller.telefono}")
    return "\n".join(lineas)


def mensaje_terminado(orden, taller) -> str:
    """Aviso al cliente de que su moto está lista, con detalle y total."""
    m = orden.moto
    total = total_a_pagar(orden, taller)
    es_lavado = getattr(orden, "es_lavado", False)
    if es_lavado:
        lineas = [
            f"Hola {orden.cliente.nombre}, tu moto {m.marca} (placa {m.placa}) ya está lavada y lista para recoger.",
        ]
        if orden.lavado_incluye:
            lineas.append(f"Lavado: {orden.lavado_incluye}")
    else:
        observaciones = orden.diagnostico or orden.observaciones or "Trabajo realizado."
        lineas = [
            f"Hola {orden.cliente.nombre}, tu moto {m.marca} (placa {m.placa}) ya está lista para recoger.",
            f"Observaciones: {observaciones}",
        ]
    lineas.append(f"Valor a pagar: ${total:,.0f}")
    lineas.append(f"Gracias por confiar en {taller.nombre}.")
    if taller.telefono:
        lineas.append(f"Contacto: {taller.telefono}")
    return "\n".join(lineas)
