"""Servidor REST del inventario RPG integrado con SWI-Prolog mediante PySwip.

El servidor usa únicamente la biblioteca estándar de Python para que la entrega
sea reproducible sin depender de un framework adicional. PySwip es la única
dependencia externa y conecta esta API con el motor lógico del archivo .pl.
"""

# argparse permite configurar host y puerto desde la terminal sin editar código.
import argparse
# json serializa las variables unificadas en una respuesta JSON válida.
import json
# mimetypes identifica el tipo de contenido de los archivos del frontend.
import mimetypes
# os permite leer HOST y PORT como variables de entorno.
import os
# re valida el identificador que se convierte en un átomo de Prolog.
import re
# sys permite enviar los logs del servidor a la consola.
import sys
# unicodedata normaliza acentos antes de consultar el átomo almacenado.
import unicodedata
# HTTPStatus hace legibles los códigos HTTP utilizados por la API.
from http import HTTPStatus
# BaseHTTPRequestHandler implementa las operaciones GET y OPTIONS.
from http.server import BaseHTTPRequestHandler, HTTPServer
# Path resuelve rutas sin depender del directorio desde el que se inicia Python.
from pathlib import Path
# parse_qs y urlparse separan la ruta y el parámetro item de la URL.
from urllib.parse import parse_qs, urlparse

# Prolog es el puente de PySwip hacia el motor SWI-Prolog.
from pyswip import Prolog


# Define la raíz del proyecto a partir de backend/app.py.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Define la ubicación del motor lógico que el backend debe consultar.
PROLOG_FILE = PROJECT_ROOT / "prolog" / "inventario.pl"
# Define la carpeta pública que contiene HTML, CSS y JavaScript.
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Crea una única instancia del motor para cargar el archivo .pl una sola vez.
prolog = Prolog()
# consult/1 carga los hechos y reglas antes de aceptar peticiones HTTP.
prolog.consult(str(PROLOG_FILE))


def normalizar_item(valor: str) -> str:
    """Convierte el texto del formulario al átomo seguro usado por Prolog.

    Se aceptan letras, números, espacios y guion bajo. Los espacios múltiples
    se convierten en guion bajo y los acentos se eliminan para que, por ejemplo,
    ``poción roja`` consulte el átomo ``pocion_roja``.
    """

    # Quita espacios externos y convierte el texto a minúsculas.
    texto = valor.strip().lower()
    # Descompone caracteres acentuados y elimina sus marcas diacríticas.
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    # Convierte cualquier grupo de espacios en un único guion bajo.
    texto = re.sub(r"\s+", "_", texto)
    # Rechaza caracteres que no pertenecen al formato de átomo permitido.
    if not texto or not re.fullmatch(r"[a-z0-9_]+", texto):
        raise ValueError(
            "El item solo puede contener letras, números, espacios o guion bajo."
        )
    # Devuelve la forma canónica que se enviará a la consulta de Prolog.
    return texto


def citar_atomo_prolog(valor: str) -> str:
    """Devuelve un átomo Prolog entre comillas simples y con comillas escapadas."""

    # La normalización ya restringe los caracteres, pero el escape mantiene la
    # construcción segura si la validación cambia en el futuro.
    return "'" + valor.replace("'", "''") + "'"


def texto_json(valor) -> str:
    """Convierte átomos o bytes devueltos por PySwip a texto JSON."""

    # Algunas versiones de PySwip devuelven bytes para ciertos átomos.
    if isinstance(valor, bytes):
        return valor.decode("utf-8")
    # str conserva el contenido de los átomos y permite serializarlo con json.
    return str(valor)


def lista_json(valor) -> list[str]:
    """Convierte una lista Prolog en una lista de strings de Python."""

    # Itera sobre la lista unificada y convierte cada elemento de forma explícita.
    return [texto_json(item) for item in list(valor)]


def consultar_inventario(item: str) -> dict | None:
    """Ejecuta procesar_inventario/5 y devuelve sus variables unificadas.

    El ItemBuscado se pasa como átomo citado; las otras cuatro variables quedan
    libres para que Prolog las unifique con TotalItems y las listas solicitadas.
    ``None`` representa una consulta válida cuyo item no pertenece al inventario.
    """

    # Construye la consulta sin concatenar texto sin validar del usuario.
    consulta = (
        "procesar_inventario("
        f"{citar_atomo_prolog(item)}, "
        "TotalItems, InventarioInvertido, InventarioUnico, InventarioOrdenado)"
    )
    # maxresult=1 evita repetir la misma respuesta si Prolog recibe backtracking.
    soluciones = list(prolog.query(consulta, maxresult=1))
    # Un fallo de member/2 significa que el item no fue encontrado.
    if not soluciones:
        return None
    # Extrae la única solución unificada devuelta por PySwip.
    solucion = soluciones[0]
    # Mapea explícitamente los nombres de Prolog a claves JSON estables.
    return {
        "ok": True,
        "item_buscado": item,
        "total_items": int(solucion["TotalItems"]),
        "inventario_invertido": lista_json(solucion["InventarioInvertido"]),
        "inventario_unico": lista_json(solucion["InventarioUnico"]),
        "inventario_ordenado": lista_json(solucion["InventarioOrdenado"]),
    }


class CORSRequestHandler(BaseHTTPRequestHandler):
    """Manejador HTTP con CORS aplicado de forma centralizada a cada respuesta."""

    # Identifica el servicio en la cabecera Server sin revelar datos del sistema.
    server_version = "InventarioRPG/1.0"

    def end_headers(self) -> None:
        """Añade las cabeceras CORS antes de cerrar cualquier respuesta."""

        # Permite que el frontend se sirva desde otro origen durante la revisión.
        self.send_header("Access-Control-Allow-Origin", "*")
        # Declara los métodos admitidos por el recurso REST.
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        # Declara las cabeceras que un navegador puede enviar.
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        # Finaliza la sección de cabeceras usando la implementación base.
        super().end_headers()

    def do_OPTIONS(self) -> None:
        """Responde el preflight CORS sin ejecutar una consulta Prolog."""

        # 204 confirma que el navegador puede continuar con el GET.
        self.send_response(HTTPStatus.NO_CONTENT)
        # El método base añade las cabeceras CORS de forma uniforme.
        self.end_headers()

    def do_GET(self) -> None:
        """Enruta los recursos estáticos y el endpoint GET de inventario."""

        # Divide la URL en ruta y parámetros de consulta.
        url = urlparse(self.path)
        # Conserva solo el primer valor de item para una petición determinista.
        parametros = parse_qs(url.query)

        # Sirve el frontend desde el mismo proceso para facilitar la evaluación.
        if url.path == "/":
            self.enviar_archivo(FRONTEND_DIR / "index.html")
            return
        # Sirve JavaScript y CSS sin exponer rutas fuera de frontend/.
        if url.path == "/app.js":
            self.enviar_archivo(FRONTEND_DIR / "app.js")
            return
        if url.path == "/styles.css":
            self.enviar_archivo(FRONTEND_DIR / "styles.css")
            return
        # Sirve la evidencia visual de la respuesta GET real para documentar la API.
        if url.path == "/evidencias/api-evidence.html":
            self.enviar_archivo(PROJECT_ROOT / "evidencias" / "api-evidence.html")
            return
        # Sirve el registro visual de consola generado durante la ejecución comprobada.
        if url.path == "/evidencias/console-evidence.html":
            self.enviar_archivo(PROJECT_ROOT / "evidencias" / "console-evidence.html")
            return
        # Expone un health check independiente de la consulta de inventario.
        if url.path == "/api/health":
            self.enviar_json({"ok": True, "servicio": "inventario-rpg"}, HTTPStatus.OK)
            return
        # El endpoint principal exige el parámetro GET item.
        if url.path == "/api/inventario":
            self.atender_consulta(parametros.get("item", [""])[0])
            return
        # Todas las demás rutas responden 404 en JSON para mantener el contrato API.
        self.enviar_json(
            {"ok": False, "error": "Ruta no encontrada."}, HTTPStatus.NOT_FOUND
        )

    def atender_consulta(self, item_sin_normalizar: str) -> None:
        """Valida el parámetro, ejecuta Prolog y serializa su resultado."""

        # Rechaza la ausencia del parámetro con un error claro para el cliente.
        if not item_sin_normalizar.strip():
            self.enviar_json(
                {"ok": False, "error": "Debe enviar el parámetro GET item."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            # Normaliza y valida antes de construir la consulta de Prolog.
            item = normalizar_item(item_sin_normalizar)
        except ValueError as error:
            # Devuelve 400 sin iniciar una consulta con entrada inválida.
            self.enviar_json(
                {"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST
            )
            return

        try:
            # Ejecuta la regla principal y recibe sus variables unificadas.
            resultado = consultar_inventario(item)
        except Exception as error:  # pragma: no cover - protección del servidor.
            # Registra el fallo en consola para que sea diagnosticable.
            print(f"[Backend] Error consultando Prolog: {error}", file=sys.stderr)
            # Evita enviar un traceback al navegador, pero mantiene respuesta JSON.
            self.enviar_json(
                {"ok": False, "error": "No fue posible consultar el motor lógico."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        # member/2 puede fallar sin ser un error del servidor.
        if resultado is None:
            self.enviar_json(
                {"ok": False, "item_buscado": item, "error": "Item no encontrado."},
                HTTPStatus.NOT_FOUND,
            )
            return
        # Envía las listas calculadas por Prolog sin quemar valores en el frontend.
        self.enviar_json(resultado, HTTPStatus.OK)

    def enviar_json(self, payload: dict, status: HTTPStatus) -> None:
        """Escribe un diccionario como JSON UTF-8 con el código HTTP indicado."""

        # Serializa datos reales de Prolog conservando caracteres no ASCII.
        contenido = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        # Indica al cliente que la respuesta es JSON y usa UTF-8.
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        # Cierra las cabeceras y aplica CORS desde end_headers/0.
        self.end_headers()
        # Escribe el cuerpo JSON en el socket HTTP.
        self.wfile.write(contenido)

    def enviar_archivo(self, archivo: Path) -> None:
        """Sirve un archivo estático existente o responde 404."""

        # Verifica que la ruta esperada sea un archivo regular.
        if not archivo.is_file():
            self.enviar_json(
                {"ok": False, "error": "Archivo estático no encontrado."},
                HTTPStatus.NOT_FOUND,
            )
            return
        # Lee el archivo en binario para conservar exactamente su contenido.
        contenido = archivo.read_bytes()
        # Obtiene un MIME razonable y usa octet-stream como respaldo.
        tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        # Envía la respuesta estática con su tamaño para que el navegador la cierre.
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        # Aplica las cabeceras CORS antes de cerrar la respuesta.
        self.end_headers()
        # Transfiere el contenido al navegador.
        self.wfile.write(contenido)

    def log_message(self, formato: str, *argumentos) -> None:
        """Formato compacto de logs para evidenciar las peticiones recibidas."""

        # Reemplaza el logger genérico con una etiqueta útil para la captura.
        mensaje = formato % argumentos
        print(f"[Backend] {self.command} {self.path} - {mensaje}", file=sys.stderr)


def argumentos_cli() -> argparse.Namespace:
    """Lee la configuración de ejecución sin obligar a editar app.py."""

    # Crea el parser de argumentos del ejecutable.
    parser = argparse.ArgumentParser(description="API REST del inventario RPG")
    # Permite cambiar el host para pruebas locales o conexiones externas.
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    # Permite cambiar el puerto si el valor por defecto está ocupado.
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5000")))
    # Devuelve los argumentos parseados por argparse.
    return parser.parse_args()


def main() -> None:
    """Inicia el servidor HTTP hasta que el usuario presione Ctrl+C."""

    # Obtiene host y puerto desde la CLI o variables de entorno.
    configuracion = argumentos_cli()
    # HTTPServer mantiene un solo hilo para que el motor Prolog sea determinista.
    servidor = HTTPServer((configuracion.host, configuracion.port), CORSRequestHandler)
    # Publica una instrucción de prueba visible en la terminal del backend.
    print(
        f"[Backend] API lista en http://127.0.0.1:{configuracion.port} "
        "(Ctrl+C para detener)",
        flush=True,
    )
    try:
        # Atiende peticiones GET y OPTIONS de forma continua.
        servidor.serve_forever()
    except KeyboardInterrupt:
        # Permite una salida limpia al detener el proceso desde la terminal.
        print("\n[Backend] Servidor detenido.", flush=True)
    finally:
        # Libera el socket aunque el proceso termine por una interrupción.
        servidor.server_close()


# Ejecuta main/0 únicamente cuando este archivo se inicia como programa.
if __name__ == "__main__":
    main()
