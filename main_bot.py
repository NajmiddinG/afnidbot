import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy.orm import sessionmaker
from create_db import Contact, engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the bot token from the environment
TOKEN = getenv('BOT_TOKEN')

# Set up the database session
Session = sessionmaker(bind=engine)
session = Session()

# Initialize Dispatcher
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    """
    This handler receives messages with `/start` command.
    """
    contact_button = KeyboardButton(text="📞 Kontaktni ulashish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],  # Define the keyboard layout
        resize_keyboard=True
    )
    
    await message.answer(
        "Davom etish uchun 📞 kontaktingizni ulashing",
        reply_markup=reply_markup
    )

@dp.message(Command("data"))
async def data_handler(message: Message) -> None:
    """
    This handler receives messages with `/data` command and displays all contacts.
    """
    if str(message.from_user.id) not in list(getenv("ADMIN_IDS").split(",")):
        await message.answer("🚫 Sizga ruxsat berilmagan!")
        return
    SUPERADMIN_TELEGRAM_ID = int(getenv("SUPERADMIN_TELEGRAM_ID"))
    contacts = session.query(Contact).filter(Contact.telegram_id != SUPERADMIN_TELEGRAM_ID).all()
    if contacts:
        response = "<b>📋 Ro'yxatdagi kontaktlar:</b>\n=========================\n"
        for index, contact in enumerate(contacts, start=1):
            response += (
                f"<b><i>🆔 №:</i></b> {index}\n"
                f"<b><i>🔤 Ism:</i></b> {contact.ism or '🚫 mavjud emas'}\n"
                f"<b><i>🔤 Familiya:</i></b> {contact.familiya or '🚫 mavjud emas'}\n"
                f"<b><i>👤 Username:</i></b> @{contact.username or '🚫 mavjud emas'}\n"
                f"<b><i>📞 Telefon raqam:</i></b> {contact.telefon_raqam}\n"
                f"<b><i>🆔 Telegram ID:</i></b> {contact.telegram_id}\n"
                f"=========================\n"
            )
        await message.answer(response)
    else:
        await message.answer("🚫 Hozirda hech qanday kontakt mavjud emas.")

@dp.message(lambda message: message.content_type == ContentType.CONTACT)
async def contact_handler(message: Message) -> None:
    """
    This handler processes the user's contact information.
    """
    contact = message.contact
    telegram_id = message.from_user.id
    telefon_raqam = contact.phone_number
    username = message.from_user.username
    ism = message.from_user.first_name
    familiya = message.from_user.last_name

    # Check if the contact already exists
    existing_contact = session.query(Contact).filter_by(telegram_id=telegram_id).first()

    if existing_contact:
        # Update the existing contact
        existing_contact.telefon_raqam = telefon_raqam
        existing_contact.username = username
        existing_contact.ism = ism
        existing_contact.familiya = familiya
    else:
        # Insert new contact
        new_contact = Contact(
            telegram_id=telegram_id,
            telefon_raqam=telefon_raqam,
            username=username,
            ism=ism,
            familiya=familiya
        )
        session.add(new_contact)

    session.commit()

    await message.answer("✅ Muvafaqqiyatli amalga oshirildi!")

async def main() -> None:
    # Initialize Bot instance with default bot properties
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
