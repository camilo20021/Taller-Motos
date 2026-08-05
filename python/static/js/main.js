document.addEventListener("DOMContentLoaded", () => {
  // Menú lateral deslizable en tablet/celular (botón hamburguesa).
  const menuBtn = document.getElementById("menuBtn");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlayMenu");
  if (menuBtn && sidebar && overlay) {
    const abrir = () => {
      sidebar.classList.add("abierto");
      overlay.classList.add("visible");
    };
    const cerrar = () => {
      sidebar.classList.remove("abierto");
      overlay.classList.remove("visible");
    };
    menuBtn.addEventListener("click", () =>
      sidebar.classList.contains("abierto") ? cerrar() : abrir()
    );
    overlay.addEventListener("click", cerrar);
    // Al tocar una opción del menú, se cierra solo.
    sidebar.querySelectorAll("nav a").forEach((a) => a.addEventListener("click", cerrar));
  }

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

  // Nueva orden: mostrar campos de Reparación o de Lavado según el tipo elegido.
  const tipoOrden = document.getElementById("tipoOrden");
  if (tipoOrden) {
    const form = document.getElementById("formOrden");
    const aplicarTipo = () => {
      const seleccion = form.querySelector('input[name="tipo"]:checked');
      const esLavado = seleccion && seleccion.value === "lavado";
      form.querySelectorAll(".solo-lavado").forEach((el) => {
        el.style.display = esLavado ? "" : "none";
      });
      form.querySelectorAll(".solo-reparacion").forEach((el) => {
        el.style.display = esLavado ? "none" : "";
      });
      tipoOrden.querySelectorAll(".tipo-opcion").forEach((l) => {
        l.classList.toggle("activa", l.querySelector("input").checked);
      });
    };
    tipoOrden.querySelectorAll('input[name="tipo"]').forEach((r) =>
      r.addEventListener("change", aplicarTipo)
    );
    aplicarTipo();
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
