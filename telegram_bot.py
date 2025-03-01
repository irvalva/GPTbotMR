import os
import json
import logging
import asyncio
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

# Cargar información adicional desde JSON
def cargar_informacion():
    try:
        with open("informacion.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error al cargar informacion.json: {e}")
        return {}

INFO = cargar_informacion()

# Función para mejorar el mensaje antes de enviarlo
def mejorar_mensaje(mensaje):
    prompt = f"Mejora este mensaje manteniendo un tono cálido, persuasivo y alineado con la misión de Padre Mateo:\n\n{mensaje}"
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Función para procesar mensajes
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text.strip()

    # Contexto inicial para definir el rol del bot
    contexto = [
        {"role": "system", "content": INFO.get("mision", "Eres el Padre Mateo Rodríguez, un sacerdote dedicado a ayudar.")},
        {"role": "system", "content": f"Datos de donaciones: {INFO['donaciones']['transferencia']}"},
        {"role": "system", "content": f"Productos solidarios disponibles: {', '.join(INFO['donaciones']['productos_solidarios'])}"},
        {"role": "user", "content": user_message}
    ]

    # Generar respuesta con GPT
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=contexto
        )
        respuesta = response.choices[0].message.content

        # Mejorar el mensaje antes de enviarlo
        respuesta = mejorar_mensaje(respuesta)

        # Calcular retraso según la longitud del mensaje
        retraso = min(1.5 + (len(respuesta) / 100), 5)
        await asyncio.sleep(retraso)

        await update.message.reply_text(respuesta)

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
