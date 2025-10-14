import os
from uuid import uuid4
from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from src.audio_processor import ProcessingStatus, UniqueMusicStorageApp


class SijufyDedupBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp = Dispatcher()
        self._register_handlers()
        self.audio_processor = UniqueMusicStorageApp(
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.04"))
        )
        self.supported_extensions = ("wav", "mp3", "flac", "ogg", "m4a")

    def _register_handlers(self):
        self.dp.message(Command("start"))(self.command_start_handler)
        self.dp.message(F.content_type.in_({"audio"}))(self.handle_audio_message)

    async def command_start_handler(self, message: Message) -> None:
        await message.answer("Hello! I'm a bot created with aiogram.")

    async def handle_audio_message(self, message: Message) -> None:
        file_ext = message.audio.file_name.split(".")[-1]
        if file_ext not in self.supported_extensions:
            await message.answer("Audio is not supported.")
            return

        sample_dir = "temp"
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)
        unique_id = uuid4()
        file_path = f"temp/{str(unique_id)}.{file_ext}"
        await self.download(message.audio.file_id, file_path)
        processing_status = self.audio_processor.process_and_add_track(file_path)
        os.remove(file_path)
        if processing_status == ProcessingStatus.UNIQUE:
            return
        elif processing_status == ProcessingStatus.ERROR:
            message.answer("An error occurred while processing the audio.")
        elif processing_status == ProcessingStatus.DUPLICATE:
            await self.delete_message(message.chat.id, message.message_id)

    async def start(self):
        await self.dp.start_polling(self)
