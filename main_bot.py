import os
import sys
import signal
import asyncio
import logging
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from sqlalchemy.orm import sessionmaker
from create_db import Contact, engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the bot token from the environment
TOKEN = getenv('BOT_TOKEN')


# PID file setup
PID_FILE = '/tmp/aiogram_bot_afnid.pid'
def cleanup_pid_file():
    """Remove the PID file if it exists."""
    if os.path.isfile(PID_FILE):
        os.remove(PID_FILE)

def handle_exit(signum, frame):
    """Handle termination signals and clean up before exiting."""
    print(f"Received signal {signum}. Exiting...")
    cleanup_pid_file()
    sys.exit(0)

# Register signal handlers for clean termination
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def check_and_create_pid_file():
    """Check if the PID file exists and verify if the process is still running."""
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, 'r') as f:
            old_pid = f.read().strip()
        
        try:
            os.kill(int(old_pid), 0)  # Sends signal 0 to check if the process is alive
            print(f"Another instance is running with PID {old_pid}. Exiting.")
            sys.exit()
        except (OSError, ValueError):
            print("Stale PID file found. Removing and starting a new instance.")
            cleanup_pid_file()
    
    # Create the PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

# Check and create PID file
check_and_create_pid_file()

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
    # Create a "Run the bot" button
    run_button = KeyboardButton(text="▶️ Botni ishga tushirish")
    run_markup = ReplyKeyboardMarkup(
        keyboard=[[run_button]],  # Define the keyboard layout
        resize_keyboard=True
    )

    # Compose the welcome message template
    welcome_message = (
        f"Assalomu alaykum, {message.from_user.first_name} 👋\n"
        "🤖 Evosning ushbu rasmiy botidan foydalanish orqali 50% chegirmani qo'lga kiriting!\n\n"
        "👇 Pastdagi 'Botni ishga tushirish' tugmasini bosing."
    )

    # Send the welcome message with the "Run the bot" button
    await message.answer(
        welcome_message,
        reply_markup=run_markup
    )

@dp.message(lambda message: message.text == "▶️ Botni ishga tushirish")
async def run_bot(message: Message) -> None:
    """
    This handler asks for the user's contact after they click "Run the bot".
    """
    # Create a contact button
    contact_button = KeyboardButton(text="📞 Kontaktni ulashish", request_contact=True)
    contact_markup = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],  # Define the keyboard layout
        resize_keyboard=True
    )

    # Send the message asking for the contact
    await message.answer(
        "Davom etish uchun 📞 kontaktingizni ulashing.",
        reply_markup=contact_markup
    )

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

    await message.answer("✅ Muvafaqqiyatli amalga oshirildi!", reply_markup=ReplyKeyboardRemove())

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


async def main() -> None:
    # Initialize Bot instance with default bot properties
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    finally:
        cleanup_pid_file()
