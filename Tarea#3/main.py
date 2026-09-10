from __future__ import annotations

import os
import random
import re
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
COMMANDS = {
    "/hola": "saluda usando el nombre de Telegram",
    "/hora": "muestra la fecha y hora actual",
    "/contacto": "muestra la información de contacto del grupo",
    "/integrantes": "muestra los integrantes y sus carnés",
    "/ayuda": "muestra los comandos disponibles",
    "/menu": "muestra el menú interactivo",
    "/calcular": "realiza suma, resta, multiplicación o división",
    "/tabla": "muestra la tabla de multiplicar del 1 al 10",
    "/convertir": "convierte entre cm, m, km, mi y ft",
    "/aleatorio": "genera un entero dentro de un rango",
}
NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
UNIT_FACTORS = {
    "cm": Decimal("0.01"),
    "m": Decimal("1"),
    "km": Decimal("1000"),
    "mi": Decimal("1609.344"),
    "ft": Decimal("0.3048"),
}
UNIT_ALIASES = {
    "centimetro": "cm",
    "centimetros": "cm",
    "metro": "m",
    "metros": "m",
    "kilometro": "km",
    "kilometros": "km",
    "milla": "mi",
    "millas": "mi",
    "pie": "ft",
    "pies": "ft",
}
MENU = {
    "inline_keyboard": [
        [
            {"text": " Hola", "callback_data": "hola"},
            {"text": " Hora", "callback_data": "hora"},
        ],
        [
            {"text": " Contacto", "callback_data": "contacto"},
            {"text": " Integrantes", "callback_data": "integrantes"},
        ],
        [
            {"text": " Ayuda", "callback_data": "ayuda"},
            {"text": " Calcular", "callback_data": "calcular"},
        ],
        [
            {"text": " Tabla", "callback_data": "tabla"},
            {"text": " Convertir", "callback_data": "convertir"},
        ],
        [{"text": " Aleatorio", "callback_data": "aleatorio"}],
    ]
}


class TelegramError(RuntimeError):
    """Error devuelto por Telegram o por la conexión HTTP."""


load_dotenv(PROJECT_DIR / ".env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
TIMEZONE = os.getenv("TIMEZONE", "America/Guatemala").strip() or "America/Guatemala"
CONTACT_INFO = os.getenv(
    "CONTACT_INFO",
    "Contacto no configurado: define CONTACT_INFO en el archivo .env.",
).strip()
GROUP_LINK = os.getenv("TELEGRAM_GROUP_LINK", "").strip()
MEMBERS = os.getenv(
    "MEMBERS",
    "Integrantes no configurados: define MEMBERS en el archivo .env.",
).strip()


def entero_env(nombre: str, predeterminado: int) -> int:
    try:
        return max(1, int(os.getenv(nombre, str(predeterminado))))
    except ValueError:
        return predeterminado


POLL_TIMEOUT = entero_env("POLL_TIMEOUT", 30)


def telegram_request(method: str, payload: dict | None = None, timeout: int = 20):
    """Ejecuta un método de la API de Telegram y devuelve su resultado."""

    if not TELEGRAM_TOKEN:
        raise TelegramError("Falta TELEGRAM_TOKEN en las variables de entorno.")
    try:
        response = requests.post(
            f"{API_URL}/{method}",
            json=payload or {},
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()
    except requests.HTTPError as error:
        detalle = error.response.text if error.response is not None else str(error)
        codigo = error.response.status_code if error.response is not None else "?"
        raise TelegramError(f"HTTP {codigo}: {detalle}") from error
    except requests.RequestException as error:
        raise TelegramError(f"No fue posible conectar con Telegram: {error}") from error
    except ValueError as error:
        raise TelegramError("Telegram devolvió una respuesta inválida.") from error
    if not result.get("ok"):
        raise TelegramError(result.get("description", "Telegram rechazó la solicitud."))
    return result.get("result")


def enviar_mensaje(chat_id: int, texto: str, markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": texto}
    if markup is not None:
        payload["reply_markup"] = markup
    telegram_request("sendMessage", payload)


def responder_error(chat_id: int, mensaje: str) -> None:
    enviar_mensaje(chat_id, f" {mensaje}")


def nombre_telegram(usuario: dict | None) -> str:
    usuario = usuario or {}
    nombre = " ".join(
        parte for parte in (usuario.get("first_name"), usuario.get("last_name")) if parte
    ).strip()
    return nombre or usuario.get("username") or "usuario"


def zona_horaria() -> ZoneInfo:
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        return ZoneInfo("UTC")


def parsear_decimal(valor: str) -> Decimal:
    if not NUMBER_PATTERN.fullmatch(valor):
        raise ValueError(f"'{valor}' no es un número válido.")
    try:
        numero = Decimal(valor)
    except InvalidOperation as error:
        raise ValueError(f"'{valor}' no es un número válido.") from error
    if not numero.is_finite():
        raise ValueError(f"'{valor}' no es un número válido.")
    return numero


def formatear_decimal(numero: Decimal) -> str:
    if numero == 0:
        return "0"
    texto = format(numero.normalize(), "f")
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def calcular(args: list[str]) -> str:
    if len(args) != 3:
        raise ValueError("Uso correcto: /calcular <numero1> <operador> <numero2>")
    primero = parsear_decimal(args[0])
    operador = args[1].lower()
    segundo = parsear_decimal(args[2])
    if operador == "+":
        resultado = primero + segundo
    elif operador == "-":
        resultado = primero - segundo
    elif operador in {"*", "x", "×"}:
        resultado = primero * segundo
    elif operador == "/":
        if segundo == 0:
            raise ValueError("No se puede dividir entre cero.")
        resultado = primero / segundo
    else:
        raise ValueError("Operador inválido. Usa +, -, * o /.")
    return (
        f"Resultado: {formatear_decimal(primero)} {args[1]} "
        f"{formatear_decimal(segundo)} = {formatear_decimal(resultado)}"
    )


def parsear_entero(valor: str) -> int:
    if not INTEGER_PATTERN.fullmatch(valor):
        raise ValueError(f"'{valor}' debe ser un número entero.")
    return int(valor)


def tabla(args: list[str]) -> str:
    if len(args) != 1:
        raise ValueError("Uso correcto: /tabla <numero>")
    numero = parsear_entero(args[0])
    return "Tabla del {}:\n{}".format(
        numero,
        "\n".join(
            f"{numero} x {multiplicador} = {numero * multiplicador}"
            for multiplicador in range(1, 11)
        ),
    )


def unidad_canonica(unidad: str) -> str:
    unidad = UNIT_ALIASES.get(unidad.lower(), unidad.lower())
    if unidad not in UNIT_FACTORS:
        raise ValueError("Unidad inválida. Usa cm, m, km, mi o ft.")
    return unidad


def convertir(args: list[str]) -> str:
    if len(args) != 3:
        raise ValueError(
            "Uso correcto: /convertir <cantidad> <unidad_origen> <unidad_destino>"
        )
    cantidad = parsear_decimal(args[0])
    origen = unidad_canonica(args[1])
    destino = unidad_canonica(args[2])
    resultado = cantidad * UNIT_FACTORS[origen] / UNIT_FACTORS[destino]
    return (
        f"Conversión: {formatear_decimal(cantidad)} {origen} = "
        f"{formatear_decimal(resultado)} {destino}"
    )


def aleatorio(args: list[str]) -> str:
    if len(args) != 2:
        raise ValueError("Uso correcto: /aleatorio <min> <max>")
    minimo = parsear_entero(args[0])
    maximo = parsear_entero(args[1])
    if minimo > maximo:
        raise ValueError("El mínimo no puede ser mayor que el máximo.")
    return f"Número aleatorio entre {minimo} y {maximo}: {random.randint(minimo, maximo)}"


def texto_ayuda() -> str:
    lineas = ["Comandos disponibles:"]
    lineas.extend(f"{comando}: {descripcion}." for comando, descripcion in COMMANDS.items())
    lineas.extend(
        [
            "",
            "Ejemplos:",
            "/calcular 12 * 3",
            "/tabla 7",
            "/convertir 1 km m",
            "/aleatorio 1 100",
        ]
    )
    return "\n".join(lineas)


def texto_contacto() -> str:
    texto = f"Contacto del grupo:\n{CONTACT_INFO}"
    if GROUP_LINK:
        texto += f"\nEnlace de Telegram: {GROUP_LINK}"
    return texto


def texto_menu() -> str:
    return "Selecciona una opción o usa /ayuda para ver los formatos de los comandos:"


def comando_desde_texto(texto: str) -> tuple[str, list[str]]:
    partes = texto.strip().split()
    if not partes or not partes[0].startswith("/"):
        raise ValueError("Escribe un comando. Usa /ayuda para ver las opciones disponibles.")
    comando = partes[0].split("@", 1)[0].lower()
    return comando, partes[1:]


def manejar_comando(chat_id: int, texto: str, usuario: dict | None = None) -> None:
    try:
        comando, args = comando_desde_texto(texto)
        if comando == "/start":
            enviar_mensaje(
                chat_id,
                f"Hola, {nombre_telegram(usuario)}. Soy el bot de la Tarea 03.",
                MENU,
            )
        elif comando == "/hola":
            if args:
                raise ValueError("Uso correcto: /hola")
            enviar_mensaje(chat_id, f"¡Hola, {nombre_telegram(usuario)}!")
        elif comando == "/hora":
            if args:
                raise ValueError("Uso correcto: /hora")
            ahora = datetime.now(zona_horaria())
            enviar_mensaje(
                chat_id,
                f"Fecha y hora actual ({TIMEZONE}): {ahora:%d/%m/%Y %H:%M:%S}",
            )
        elif comando == "/contacto":
            if args:
                raise ValueError("Uso correcto: /contacto")
            enviar_mensaje(chat_id, texto_contacto())
        elif comando == "/integrantes":
            if args:
                raise ValueError("Uso correcto: /integrantes")
            enviar_mensaje(chat_id, f"Integrantes del grupo:\n{MEMBERS}")
        elif comando == "/ayuda":
            if args:
                raise ValueError("Uso correcto: /ayuda")
            enviar_mensaje(chat_id, texto_ayuda())
        elif comando == "/menu":
            if args:
                raise ValueError("Uso correcto: /menu")
            enviar_mensaje(chat_id, texto_menu(), MENU)
        elif comando == "/calcular":
            enviar_mensaje(chat_id, calcular(args))
        elif comando == "/tabla":
            enviar_mensaje(chat_id, tabla(args))
        elif comando == "/convertir":
            enviar_mensaje(chat_id, convertir(args))
        elif comando == "/aleatorio":
            enviar_mensaje(chat_id, aleatorio(args))
        else:
            responder_error(chat_id, f"Comando inexistente: {comando}. Usa /ayuda.")
    except ValueError as error:
        responder_error(chat_id, str(error))
    except TelegramError as error:
        print(f"[Telegram] No se pudo responder en {chat_id}: {error}", flush=True)


def manejar_callback(callback: dict) -> None:
    callback_id = callback.get("id")
    if callback_id:
        try:
            telegram_request("answerCallbackQuery", {"callback_query_id": callback_id})
        except TelegramError as error:
            print(f"[Telegram] No se pudo confirmar el botón: {error}", flush=True)
    try:
        mensaje = callback.get("message") or {}
        chat = mensaje.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return
        accion = callback.get("data", "")
        if f"/{accion}" in COMMANDS:
            manejar_comando(chat_id, f"/{accion}", callback.get("from"))
        else:
            responder_error(chat_id, "Opción de menú no reconocida. Usa /menu.")
    except TelegramError as error:
        print(f"[Telegram] Error procesando botón: {error}", flush=True)


def manejar_actualizacion(actualizacion: dict) -> None:
    if "callback_query" in actualizacion:
        manejar_callback(actualizacion["callback_query"])
        return
    mensaje = actualizacion.get("message") or {}
    texto = mensaje.get("text")
    chat_id = (mensaje.get("chat") or {}).get("id")
    if texto and chat_id is not None:
        manejar_comando(chat_id, texto, mensaje.get("from"))


def ejecutar() -> None:
    """Valida el bot y lo mantiene disponible mediante long polling."""

    if not TELEGRAM_TOKEN:
        raise SystemExit("Configura TELEGRAM_TOKEN en Tarea#3/.env o en el entorno.")
    try:
        bot = telegram_request("getMe", timeout=15)
        telegram_request("deleteWebhook", {"drop_pending_updates": False}, timeout=15)
    except TelegramError as error:
        raise SystemExit(f"No se pudo iniciar el bot: {error}") from error

    print(f"[Bot] @{bot.get('username', 'sin_usuario')} activo.", flush=True)
    offset = 0
    while True:
        try:
            actualizaciones = telegram_request(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": POLL_TIMEOUT,
                    "allowed_updates": ["message", "callback_query"],
                },
                timeout=POLL_TIMEOUT + 10,
            ) or []
            for actualizacion in actualizaciones:
                offset = actualizacion["update_id"] + 1
                try:
                    manejar_actualizacion(actualizacion)
                except Exception as error:
                    print(f"[Bot] Error manejando actualización: {error}", flush=True)
        except (TelegramError, OSError) as error:
            print(f"[Bot] Error de conexión: {error}. Reintentando...", flush=True)
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[Bot] detenido.", flush=True)
            return


if __name__ == "__main__":
    ejecutar()
