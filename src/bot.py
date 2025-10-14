import os
import logging
from uuid import uuid4
from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from src.audio_processor import ProcessingStatus, UniqueMusicStorageApp


class SijufyDedupBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp = Dispatcher()
        self.admins = list(map(int, os.getenv("ADMIN_USER_IDS").split(",")))

        try:
            self.allowed_channel_id = int(os.getenv("ALLOWED_CHANNEL_ID"))
            logging.info(f"Bot will operate in channel ID: {self.allowed_channel_id}")
        except (ValueError, TypeError):
            logging.error(
                "ALLOWED_CHANNEL_ID is not set or is not a valid integer. The bot will not work in any channel."
            )
            self.allowed_channel_id = None

        self._register_handlers()
        self.audio_processor = UniqueMusicStorageApp(
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.04"))
        )
        self.supported_extensions = ("wav", "mp3", "flac", "ogg", "m4a")

    def _register_handlers(self):
        self.dp.message(Command("start"))(self.command_start_handler)

        self.dp.message(
            Command("clear"),
            F.from_user.id.in_(self.admins),
        )(self.command_clear_handler)

        self.dp.message(F.content_type.in_({"audio"}))(
            self.handle_private_audio_message
        )

        if self.allowed_channel_id:
            self.dp.channel_post(
                F.chat.id == self.allowed_channel_id, F.content_type.in_({"audio"})
            )(self.handle_audio_channel_post)

    async def command_start_handler(self, message: Message) -> None:
        await message.answer(
            "Hello! I am a SIJUFY audio deduplicator bot. Add me to your channel as an admin to get started."
        )

    async def command_clear_handler(self, message: Message) -> None:
        self.audio_processor.clear_db()
        await message.answer("SIJUFY Audio Deduplicator database is cleared!")

    async def handle_private_audio_message(self, message: Message) -> None:
        await message.answer("This bot is designed to work in SIJUFY channel only.")

    async def handle_audio_channel_post(self, channel_post: Message) -> None:
        if not channel_post.audio or not channel_post.audio.file_name:
            return

        file_ext = channel_post.audio.file_name.split(".")[-1]
        if file_ext not in self.supported_extensions:
            logging.warning(
                f"Unsupported audio format received: {channel_post.audio.file_name}"
            )
            return

        sample_dir = "temp"
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)

        unique_id = uuid4()
        file_path = f"temp/{str(unique_id)}.{file_ext}"

        await self.download(channel_post.audio.file_id, file_path)

        processing_status = self.audio_processor.process_and_add_track(file_path)

        os.remove(file_path)

        if processing_status == ProcessingStatus.UNIQUE:
            return
        elif processing_status == ProcessingStatus.ERROR:
            logging.error(
                f"An error occurred while processing audio: {channel_post.audio.file_name}"
            )
        elif processing_status == ProcessingStatus.DUPLICATE:
            await self.delete_message(channel_post.chat.id, channel_post.message_id)
            logging.info(
                f"Deleted duplicate audio message {channel_post.message_id} from channel {channel_post.chat.id}"
            )

    async def start(self):
        await self.dp.start_polling(self)
