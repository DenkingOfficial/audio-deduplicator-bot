from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


class SijufyDedupBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp = Dispatcher()
        self._register_handlers()

    def _register_handlers(self):
        self.dp.message(Command("start"))(self.command_start_handler)
        self.dp.message(F.content_type.in_({"audio"}))(self.handle_audio_message)

    async def command_start_handler(self, message: Message) -> None:
        await message.answer("Hello! I'm a bot created with aiogram.")

    async def handle_audio_message(self, message: Message) -> None:
        await message.answer("Audio Handler is called")

    async def start(self):
        await self.dp.start_polling(self)
