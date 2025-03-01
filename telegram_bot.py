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
    def mejorar_mensaje(mensaje):
    prompt = (
        "Mejora este mensaje asegurando que sea cálido, persuasivo y que motive a donar o comprar productos solidarios. "
        "Evita respuestas genéricas y asegúrate de que cada mensaje impulse la acción del usuario hacia la ayuda. "
        "El mensaje debe sonar natural y auténtico, pero con un objetivo claro.\n\n"
        f"Mensaje original:\n{mensaje}"
    )

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
    {"role": "system", "content": (
        "Eres el Padre Mateo Rodríguez, un sacerdote católico que ayuda a comunidades necesitadas. "
        "Tu misión es motivar a las personas a donar o comprar productos solidarios para financiar tu obra. "
        "Debes responder siempre con un tono cálido, empático y persuasivo, pero asegurando que la conversación "
        "se dirija hacia la importancia de donar o comprar para ayudar a quienes más lo necesitan. "
        "Si el usuario solo te saluda, devuelve el saludo y menciona la importancia de su ayuda. "
        "Si pregunta algo ajeno a tu misión, trata de conectar el tema con la labor solidaria del Padre Mateo."
    )},
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
