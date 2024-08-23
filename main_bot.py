from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from sqlalchemy.orm import sessionmaker
from create_db import Contact, engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get the bot token from the environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Set up the database session
Session = sessionmaker(bind=engine)
session = Session()

# Start command handler
async def start(update: Update, context: CallbackContext):
    contact_button = KeyboardButton(text="📞 Kontaktni ulashish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)
    
    await update.message.reply_text(
        "Davom etish uchun 📞 kontaktingizni ulashing",
        reply_markup=reply_markup
    )

# Handle contact information
async def contact_handler(update: Update, context: CallbackContext):
    contact = update.message.contact
    telegram_id = update.message.from_user.id
    telefon_raqam = contact.phone_number
    username = update.message.from_user.username
    ism = update.message.from_user.first_name
    familiya = update.message.from_user.last_name
    

    # Save contact information to the database
    new_contact = Contact(
        telegram_id=telegram_id,
        telefon_raqam=telefon_raqam,
        username=username,
        ism=ism,
        familiya=familiya
    )
    session.add(new_contact)
    session.commit()

    await update.message.reply_text("✅ Muvafaqqiyatli amalga oshirildi!")

def main():
    # Initialize the Application class
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
