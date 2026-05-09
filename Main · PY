"""
Main entry point for the Student Bot.
Run this file to start the bot: python main.py
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from database import init_db
from handlers import student, admin, common

# Load environment variables from .env file
load_dotenv()

# Configure logging so we can see what the bot is doing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Start the bot."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is missing. Check your .env file.")

    # Initialize the SQLite database (creates tables if they don't exist)
    init_db()
    logger.info("Database initialized.")

    # Create bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register all routers
    # Order matters: admin handlers run before student handlers
    dp.include_router(admin.router)
    dp.include_router(student.router)
    dp.include_router(common.router)

    logger.info("Bot is starting...")
    # Remove webhook in case one was set, then start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
