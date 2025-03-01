import os
import json
import logging
import openai
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

# Cargar respuestas desde el archivo JSON
def cargar_respuestas():
    try:
        with open("respuestas.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error al cargar respuestas.json: {e}")
        return {}

RESPUESTAS = cargar_respuestas()

# Base de datos de nombres comunes por género
NOMBRES_MASCULINOS = ["juan", "carlos", "pedro", "miguel", "luis", "manuel", "gonzalo"]
NOMBRES_FEMENINOS = ["maria", "ana", "luisa", "carmen", "sofia", "elena", "laura"]

# Función para detectar género según el nombre
def detectar_genero(nombre):
    nombre = nombre.lower()
    if nombre in NOMBRES_MASCULINOS:
        return "masculino"
    elif nombre in NOMBRES_FEMENINOS:
        return "femenino"
    return "desconocido"

# Diccionario para almacenar los nombres de los usuarios temporalmente
usuarios = {}

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_message = update.message.text.strip()

    # Si el usuario no ha dado su nombre, pedirlo
    if user_id not in usuarios:
        usuarios[user_id] = None  # Marcar que estamos esperando el nombre
        await update.message.reply_text(RESPUESTAS.get("preguntar_nombre", "¡Bendiciones! 🙏 ¿Con quién tengo el gusto?"))
        return

    # Si el usuario está respondiendo con su nombre, guardarlo
    if usuarios[user_id] is None:
        nombre = user_message.split()[0]  # Tomar la primera palabra como nombre
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

    # Responder usando GPT-3.5 Turbo si no hay respuesta en el JSON
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        chat_response = response.choices[0].message.content
        await update.message.reply_text(chat_response)
    except Exception as e:
        logging.error(f"Error al procesar el mensaje: {e}")
        await update.message.reply_text("Lo siento, hubo un error al procesar tu mensaje. 😢")

# Iniciar el bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("GPTbotMR está en ejecución...")
    application.run_polling()

if __name__ == "__main__":
    main()
