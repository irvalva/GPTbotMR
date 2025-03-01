import os
import json
import logging
import asyncio
import openai
from difflib import get_close_matches
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

# Configurar logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Cargar variables de entorno
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

# Cargar respuestas y datos adicionales
def cargar_json(nombre_archivo):
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error al cargar {nombre_archivo}: {e}")
        return {}

RESPUESTAS = cargar_json("respuestas.json")
INFO = cargar_json("informacion.json")

# Base de datos de nombres comunes por género
NOMBRES_MASCULINOS = ["juan", "carlos", "pedro", "miguel", "luis", "manuel", "gonzalo"]
NOMBRES_FEMENINOS = ["maria", "ana", "luisa", "carmen", "sofia", "elena", "laura"]

# Diccionario para almacenar los nombres de los usuarios
usuarios = {}

# Función para detectar el género del usuario
def detectar_genero(nombre):
    nombre = nombre.lower()
    if nombre in NOMBRES_MASCULINOS:
        return "masculino"
    elif nombre in NOMBRES_FEMENINOS:
        return "femenino"

    # Consultar a GPT si el nombre no está en la base
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"¿El nombre '{nombre}' es masculino o femenino? Responde solo con 'masculino' o 'femenino', si no estás seguro responde 'desconocido'."}]
    )
    return response.choices[0].message.content.strip().lower()

# Función para encontrar respuestas similares en respuestas.json
def encontrar_respuesta_cercana(pregunta, umbral=0.6):
    preguntas_disponibles = list(RESPUESTAS.keys())
    coincidencias = get_close_matches(pregunta, preguntas_disponibles, n=1, cutoff=umbral)
    if coincidencias:
        return RESPUESTAS.get(coincidencias[0])
    return None

# Función para mejorar la respuesta antes de enviarla
def mejorar_mensaje(mensaje):
    prompt = (
        "Mejora este mensaje asegurando que sea cálido, persuasivo y que motive a donar o comprar productos solidarios. "
        "Evita respuestas genéricas y hazlo más directo y efectivo.\n\n"
        f"Mensaje original:\n{mensaje}"
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Función principal para manejar mensajes
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_message = update.message.text.strip().lower()

    # Preguntar el nombre si es la primera vez que escribe
    if user_id not in usuarios:
        usuarios[user_id] = None  # Marcar que estamos esperando el nombre
        await update.message.reply_text(RESPUESTAS.get("preguntar_nombre", "¡Bendiciones! 🙏 ¿Con quién tengo el gusto?"))
        return

    # Si el usuario está respondiendo con su nombre, guardarlo
    if usuarios[user_id] is None:
        palabras = user_message.split()
        nombre = ""

        # Detectar el nombre en frases como "Soy Lucía" o "Me llamo Lucía"
        if "soy" in palabras:
            nombre = palabras[palabras.index("soy") + 1]
        elif "me" in palabras and "llamo" in palabras:
            nombre = palabras[palabras.index("llamo") + 1]
        else:
            nombre = palabras[0]  # Si no detecta, tomar la primera palabra

        genero = detectar_genero(nombre)
        usuarios[user_id] = {"nombre": nombre, "genero": genero}

        # Seleccionar la respuesta adecuada
        if genero == "masculino":
            respuesta = RESPUESTAS.get("bienvenida_masculino", "¡Bendiciones, hermano {nombre}! 🙏 ¿En qué puedo ayudarte hoy?").format(nombre=nombre)
        elif genero == "femenino":
            respuesta = RESPUESTAS.get("bienvenida_femenino", "¡Bendiciones, hermana {nombre}! 🙏 ¿En qué puedo ayudarte hoy?").format(nombre=nombre)
        else:
            respuesta = RESPUESTAS.get("genero_no_determinado", "¡Bendiciones, {nombre}! 🙏 ¿En qué puedo ayudarte hoy?").format(nombre=nombre)

        await update.message.reply_text(respuesta)
        return

    # Buscar respuesta en el JSON con coincidencia aproximada
    respuesta = encontrar_respuesta_cercana(user_message)

    if respuesta:
        respuesta = mejorar_mensaje(respuesta)
    else:
        # Si no hay respuesta en el JSON, generar respuesta con GPT usando el contenido de respuestas.json
        contexto = [
            {"role": "system", "content": f"Eres el padre Mateo Rodríguez, un sacerdote católico dedicado a ayudar a comunidades necesitadas. "
                                          "Tu misión es motivar a las personas a donar o comprar productos solidarios de manera cálida, empática y persuasiva, si la persona necesita ser atendido puedes hacerlo con la personalidad de un padre catolico y bendecirlo, pero siempre la intencion sera hacer que las personas donen o compren los productos solidarios. "
                                          "Utiliza respuestas similares a las siguientes en tus respuestas para mantener coherencia:"},
            {"role": "system", "content": json.dumps(RESPUESTAS, ensure_ascii=False)},  # Pasamos el JSON como referencia
            {"role": "system", "content": f"Datos de donaciones: {INFO['donaciones']['transferencia']}"},
            {"role": "system", "content": f"Productos solidarios disponibles: {', '.join(INFO['donaciones']['productos_solidarios'])}"},
            {"role": "user", "content": user_message}
        ]
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=contexto
        )
        respuesta = response.choices[0].message.content

    # Asegurar que la respuesta sea más corta
    if len(respuesta) > 300:
        respuesta = respuesta[:300] + "..."  # Cortar y hacer más directa

    # Calcular retraso según la longitud del mensaje
    retraso = min(1.5 + (len(respuesta) / 100), 5)
    await asyncio.sleep(retraso)

    await update.message.reply_text(respuesta)

# Iniciar el bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("GPTbotMR está en ejecución...")
    application.run_polling()

if __name__ == "__main__":
    main()
