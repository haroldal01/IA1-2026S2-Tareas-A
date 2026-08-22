// Define la ruta REST relativa para que la interfaz funcione en cualquier puerto del servidor.
const API_URL = window.INVENTORY_API_URL || "/api/inventario";

// Obtiene el formulario para interceptar su envío y usar fetch de forma asíncrona.
const inventoryForm = document.querySelector("#inventory-form");
// Obtiene el input que contiene el texto que se enviará como parámetro GET item.
const itemInput = document.querySelector("#item-input");
// Obtiene el botón para indicar visualmente cuándo una petición está en curso.
const submitButton = document.querySelector("#submit-button");
// Obtiene el mensaje accesible que comunica éxito, carga o error.
const statusMessage = document.querySelector("#status-message");
// Obtiene el elemento que muestra la variable TotalItems unificada por Prolog.
const totalItems = document.querySelector("#total-items");
// Obtiene la etiqueta que identifica la consulta que generó el resultado.
const queriedItem = document.querySelector("#queried-item");
// Obtiene las tres listas donde se renderizan las transformaciones del backend.
const reversedList = document.querySelector("#reversed-list");
const uniqueList = document.querySelector("#unique-list");
const sortedList = document.querySelector("#sorted-list");

// Cambia el texto y el tono del estado sin insertar HTML proveniente del usuario.
function setStatus(message, tone = "") {
  statusMessage.textContent = message;
  statusMessage.dataset.tone = tone;
}

// Crea un <li> por cada elemento recibido para que la lista sea realmente dinámica.
function renderList(listElement, items) {
  // Limpia el estado anterior antes de pintar la respuesta más reciente.
  listElement.replaceChildren();
  // Recorre el arreglo JSON sin asumir una cantidad fija de elementos.
  items.forEach((item) => {
    // Crea el nodo sin innerHTML para evitar interpretar contenido como marcado.
    const listItem = document.createElement("li");
    // textContent presenta el átomo recibido exactamente como texto visible.
    listItem.textContent = item;
    // Inserta el nodo en la lista correspondiente del DOM.
    listElement.appendChild(listItem);
  });
}

// Renderiza las variables unificadas que devuelve la respuesta de la API.
function renderResult(data) {
  // Muestra el total calculado por length/2 sin calcularlo en JavaScript.
  totalItems.textContent = String(data.total_items);
  // Identifica el parámetro que produjo la solución de Prolog.
  queriedItem.textContent = data.item_buscado;
  // Pinta reverse/2, que conserva duplicados y cambia el orden.
  renderList(reversedList, data.inventario_invertido);
  // Pinta sort/2, que ordena y elimina duplicados.
  renderList(uniqueList, data.inventario_unico);
  // Pinta msort/2, que ordena y conserva duplicados.
  renderList(sortedList, data.inventario_ordenado);
}

// Envía el formulario al endpoint GET y procesa el JSON sin valores precargados.
async function searchInventory(event) {
  // Evita que el navegador recargue la página al enviar el formulario.
  event.preventDefault();
  // Recorta espacios para no enviar una consulta vacía por accidente.
  const item = itemInput.value.trim();
  // Detiene la petición si el campo HTML required fue evadido programáticamente.
  if (!item) {
    setStatus("Escribe un ítem antes de consultar.", "error");
    itemInput.focus();
    return;
  }
  // Informa al usuario que la solicitud está viajando al backend.
  setStatus("Consultando el motor lógico...", "loading");
  // Deshabilita el botón para evitar peticiones duplicadas durante la espera.
  submitButton.disabled = true;
  submitButton.textContent = "Consultando...";
  inventoryForm.setAttribute("aria-busy", "true");
  try {
    // encodeURIComponent mantiene seguro el valor dentro de la URL GET.
    const requestUrl = `${API_URL}?item=${encodeURIComponent(item)}`;
    // fetch consume la API de forma asíncrona y solicita explícitamente JSON.
    const response = await fetch(requestUrl, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    // Convierte el cuerpo HTTP en el objeto JSON enviado por Python.
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error("El motor devolvió una respuesta que no se pudo leer.");
    }
    // Un status HTTP no exitoso o ok=false representa una consulta no resuelta.
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "La API no pudo resolver la consulta.");
    }
    // Renderiza todas las variables unificadas en el DOM.
    renderResult(data);
    // Confirma que la interfaz ya refleja la respuesta real del backend.
    setStatus("Consulta resuelta correctamente por Prolog.", "success");
  } catch (error) {
    // Muestra un error comprensible para problemas de red o de validación.
    const message = error instanceof TypeError
      ? "No se pudo conectar con el motor lógico. Intenta de nuevo."
      : error.message;
    setStatus(message || "No se pudo completar la consulta.", "error");
  } finally {
    // Reactiva el formulario aunque la petición haya terminado con error.
    submitButton.disabled = false;
    submitButton.textContent = "Buscar";
    inventoryForm.removeAttribute("aria-busy");
  }
}

// Conecta el evento submit con la función que realiza la petición REST.
inventoryForm.addEventListener("submit", searchInventory);
