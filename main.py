import asyncio
from os import getenv
from dotenv import load_dotenv

from src.bot import SijufyDedupBot

load_dotenv()

TOKEN = getenv("AUDIO_DEDUP_BOT_TOKEN")


async def main() -> None:
    bot = SijufyDedupBot(token=TOKEN)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
