# Tarea 03 - Bot interactivo de Telegram

Bot desarrollado en Python usando la API HTTP oficial de Telegram y ofrece un menú con botones inline de Telegram.

## Integrantes

| Integrante | Carné | Parte realizada |
| --- | --- | --- |
| Harold Sánchez | 202200100 | Configuración y despliegue |
| Kevin Pozuelos | 201800992 | Comandos y validaciones |
| Emilio Rivera  | 202004712 | Comandos básicos e información del bot |
| Angel Arreaga  | 202004762 | Operaciones matemáticas |
| Segio Sandoval | 202010298 | Conversión de unidades y números aleatorios |
| Juan Gerardi   | 201900532 | Menú interactivo y documentación |

## Requisitos

- Python 3.10 o superior.
- Un bot creado con [@BotFather](https://t.me/BotFather).
- Token guardado únicamente en `.env` o en las variables del servicio cloud.

`requirements.txt` instala `requests` para la API de Telegram y `python-dotenv`
para cargar el archivo `.env` en ejecuciones locales.

## Configuración y ejecución

Desde esta carpeta:

```bash
python3 -m venv .venv
source .venv/bin/activate
pytohn3 -m pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` y completa `TELEGRAM_TOKEN`, `CONTACT_INFO`,
`TELEGRAM_GROUP_LINK` y `MEMBERS`. Luego inicia el bot:

```bash
python3 main.py
```

El proceso debe mantenerse ejecutándose durante la calificación. Para un
servicio cloud configura las mismas variables de entorno y usa como comando de
inicio `python main.py`. Debe existir una sola instancia del proceso porque
Telegram entrega los mensajes de `getUpdates` a un consumidor a la vez.

## Comandos implementados

| Comando | Uso | Resultado |
| --- | --- | --- |
| `/hola` | `/hola` | Saluda usando el nombre de Telegram. |
| `/hora` | `/hora` | Muestra fecha y hora actuales dinámicamente. |
| `/contacto` | `/contacto` | Muestra contacto y enlace configurados. |
| `/integrantes` | `/integrantes` | Muestra nombres y carnés configurados. |
| `/ayuda` | `/ayuda` | Lista comandos y descripciones. |
| `/menu` | `/menu` | Muestra botones inline de Telegram. |
| `/calcular` | `/calcular 12 * 3` | Suma, resta, multiplicación y división. |
| `/tabla` | `/tabla 7` | Genera la tabla del 1 al 10. |
| `/convertir` | `/convertir 1 km m` | Convierte entre `cm`, `m`, `km`, `mi` y `ft`. |
| `/aleatorio` | `/aleatorio 1 100` | Genera un entero dentro del rango indicado. |

También se acepta `/start`. Los comandos con parámetros validan cantidad,
formato, unidades, división entre cero y rangos invertidos. Un comando
desconocido o un mensaje que no sea comando recibe un error sin detener el
proceso.

