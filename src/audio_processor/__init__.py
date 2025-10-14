from enum import Enum
import os
import librosa
import logging
from collections import defaultdict

from src.audio_processor.audio_embedder import AudioEmbedder
from src.audio_processor.vector_db_interface import VectorDB

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MODEL_SAMPLE_RATE = 32000
CHROMA_DB_PATH = "./chroma_db_chunked"
COLLECTION_NAME = "music_chunks"

CHUNK_SECONDS = 10
MIN_MATCH_COUNT = 2


class ProcessingStatus(Enum):
    UNIQUE = 1
    DUPLICATE = 2
    ERROR = 3


class UniqueMusicStorageApp:
    """The main application, now using chunking logic."""

    def __init__(self, similarity_threshold: float):
        self.embedder = AudioEmbedder()
        self.db = VectorDB(path=CHROMA_DB_PATH, collection_name=COLLECTION_NAME)
        self.threshold = similarity_threshold
        logging.info(
            f"App initialized with chunk threshold: {self.threshold} and min matches: {MIN_MATCH_COUNT}"
        )

    def _get_audio_chunks(self, file_path: str):
        """Loads an audio file and splits it into fixed-length chunks."""
        try:
            audio, sr = librosa.load(file_path, sr=MODEL_SAMPLE_RATE, mono=True)
            chunk_size = CHUNK_SECONDS * sr
            chunks = []
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i : i + chunk_size]
                if len(chunk) > chunk_size // 4:
                    chunks.append(chunk)
            return chunks
        except Exception as e:
            logging.error(f"Error chunking audio file {file_path}: {e}")
            return []

    def process_and_add_track(self, file_path: str):
        """
        Processes a track using chunking: generates embeddings for chunks, checks for
        duplicates based on chunk matches, and adds chunks to DB if unique.
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return ProcessingStatus.ERROR

        logging.info(f"Processing file: {os.path.basename(file_path)}")

        audio_chunks = self._get_audio_chunks(file_path)
        if not audio_chunks:
            logging.warning(f"No audio chunks generated for {file_path}. Skipping.")
            return ProcessingStatus.ERROR

        chunk_embeddings = [
            self.embedder.get_embedding(chunk) for chunk in audio_chunks
        ]
        chunk_embeddings = [emb for emb in chunk_embeddings if emb is not None]

        match_counts = defaultdict(int)
        for emb in chunk_embeddings:
            similar_chunk_meta = self.db.find_similar_chunk(emb, self.threshold)
            if similar_chunk_meta:
                original_file = similar_chunk_meta["original_filepath"]
                match_counts[original_file] += 1

        if match_counts:
            most_likely_match, num_matches = max(
                match_counts.items(), key=lambda item: item[1]
            )

            if num_matches >= MIN_MATCH_COUNT:
                logging.warning(
                    f"DUPLICATE DETECTED for '{os.path.basename(file_path)}'.\n"
                    f"It has {num_matches} matching chunks with the existing track "
                    f"'{os.path.basename(most_likely_match)}'. "
                    f"(Required: {MIN_MATCH_COUNT})"
                )
                return ProcessingStatus.DUPLICATE

        logging.info(
            f"Track '{os.path.basename(file_path)}' appears to be unique. Adding its chunks to the database."
        )
        self.db.add_chunks(
            original_filepath=file_path,
            embeddings=chunk_embeddings,
            chunk_indices=list(range(len(chunk_embeddings))),
        )
        return ProcessingStatus.UNIQUE

    def clear_db(self):
        self.db.client.delete_collection(name=COLLECTION_NAME)
        self.db.collection = self.db.client.create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
