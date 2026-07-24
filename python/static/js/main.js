document.addEventListener("DOMContentLoaded", () => {
  // Formularios que piden confirmación antes de enviarse (borrar, cerrar caja...)
  document.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      const mensaje = form.getAttribute("data-confirmar");
      if (mensaje && !window.confirm(mensaje)) {
        evento.preventDefault();
      }
    });
  });

  // Vista previa del precio unitario al elegir un repuesto (orden_detalle.html)
  const selectRepuesto = document.getElementById("select-repuesto");
  const previewPrecio = document.getElementById("precio-repuesto-preview");
  if (selectRepuesto && previewPrecio) {
    const actualizarPreview = () => {
      const opcion = selectRepuesto.selectedOptions[0];
      const precio = opcion ? opcion.getAttribute("data-precio") : null;
      if (precio) {
        const formateado = Number(precio).toLocaleString("es-CO", {
          maximumFractionDigits: 0,
        });
        previewPrecio.textContent = `Precio unitario: $${formateado}`;
      } else {
        previewPrecio.textContent = "";
      }
    };
    selectRepuesto.addEventListener("change", actualizarPreview);
    actualizarPreview();
  }

  // Los mensajes flash se atenúan solos después de un rato para no estorbar
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.4s ease";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 400);
    }, 6000);
  });
});
