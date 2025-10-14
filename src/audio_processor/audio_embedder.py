import numpy as np
import torch
from panns_inference import AudioTagging
from panns_inference.models import Cnn14
import logging

MODEL_SAMPLE_RATE = 32000


class AudioEmbedder:
    """A wrapper for the PANNs audio embedding model. (No changes here)"""

    def __init__(self, device="cpu"):
        self.device = device
        logging.info(f"Loading AudioTagging model on device: {self.device}")
        try:
            model_class = Cnn14(
                sample_rate=MODEL_SAMPLE_RATE,
                window_size=1024,
                hop_size=320,
                mel_bins=64,
                fmin=50,
                fmax=14000,
                classes_num=527,
            )
            self.tagger = AudioTagging(
                model=model_class, checkpoint_path=None, device=self.device
            )
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load the model: {e}")
            raise

    def get_embedding(self, audio_data: np.ndarray) -> np.ndarray:
        """Generates an embedding for the given audio data (a numpy array)."""
        if audio_data is None:
            return None

        audio_data = audio_data[None, :]
        audio_data = torch.from_numpy(audio_data).to(self.device)

        with torch.no_grad():
            _, embedding = self.tagger.inference(audio_data)

        return embedding.flatten()
