import os
import logging
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configurar logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Cargar variables de entorno
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: CallbackContext):
    """Responde al comando /start"""
    await update.message.reply_text("¡Hola! Soy GPTbotMR 🤖. Envíame un mensaje y te responderé con ChatGPT.")

async def handle_message(update: Update, context: CallbackContext):
    """Responde a los mensajes del usuario usando ChatGPT"""
    user_message = update.message.text

    try:
        # Enviar mensaje a OpenAI ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        chat_response = response["choices"][0]["message"]["content"]

        # Enviar respuesta al usuario
        await update.message.reply_text(chat_response)

    except Exception as e:
        logging.error(f"Error al procesar el mensaje: {e}")
        await update.message.reply_text("Lo siento, hubo un error al procesar tu mensaje. 😢")

def main():
    """Iniciar el bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("GPTbotMR está en ejecución...")
    application.run_polling()

if __name__ == "__main__":
    main()
