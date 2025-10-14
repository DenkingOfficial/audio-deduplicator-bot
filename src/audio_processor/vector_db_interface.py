import os
import numpy as np
import chromadb
import uuid
import logging


class VectorDB:
    """A wrapper for ChromaDB operations, now chunk-aware."""

    def __init__(self, path: str, collection_name: str):
        logging.info(f"Initializing ChromaDB at path: {path}")
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )
        logging.info(f"Using collection: '{collection_name}'")

    def add_chunks(self, original_filepath: str, embeddings: list, chunk_indices: list):
        """Adds a list of chunk embeddings for a single track to the database."""
        if not embeddings:
            return

        ids = [str(uuid.uuid4()) for _ in embeddings]
        metadatas = [
            {"original_filepath": original_filepath, "chunk_index": i}
            for i in chunk_indices
        ]

        self.collection.add(
            ids=ids, embeddings=[e.tolist() for e in embeddings], metadatas=metadatas
        )
        logging.info(
            f"Added {len(embeddings)} chunks for track '{os.path.basename(original_filepath)}'"
        )

    def find_similar_chunk(self, embedding: np.ndarray, threshold: float):
        """Queries for a single chunk."""
        if self.collection.count() == 0:
            return None

        results = self.collection.query(
            query_embeddings=[embedding.tolist()], n_results=1
        )

        if results["ids"][0] and results["distances"][0][0] <= threshold:
            return results["metadatas"][0][0]

        return None
