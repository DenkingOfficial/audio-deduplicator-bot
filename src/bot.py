from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


class SijufyDedupBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp = Dispatcher()
        self._register_handlers()

    def _register_handlers(self):
        self.dp.message(Command("start"))(self.command_start_handler)

    async def command_start_handler(self, message: Message) -> None:
        await message.answer("Hello! I'm a bot created with aiogram.")

    async def start(self):
        await self.dp.start_polling(self)
