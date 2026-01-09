"""
Embedding generation service for similarity search.

Supports both real embeddings (when FEATURE_SIM=true) and deterministic
stub embeddings for testing/development.
"""
import hashlib
import json
from typing import List

from app.core.config import settings


def _hash_to_vector(text: str, dim: int = 768) -> List[float]:
    """
    Generate a deterministic pseudo-embedding from text hash.

    This is used when FEATURE_SIM=false to provide consistent,
    deterministic vectors for testing without requiring real embedding models.

    Args:
        text: Input text to convert to vector
        dim: Dimension of output vector (default: 768)

    Returns:
        List of floats representing the pseudo-embedding
    """
    # Use SHA-256 hash for deterministic output
    hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()

    # Expand hash to desired dimension by repeating
    vector = []
    for i in range(dim):
        # Use different byte positions for each dimension
        byte_idx = i % len(hash_bytes)
        # Normalize to [-1, 1] range
        value = (hash_bytes[byte_idx] / 255.0) * 2 - 1
        vector.append(value)

    # Normalize to unit vector (for cosine similarity)
    magnitude = sum(v ** 2 for v in vector) ** 0.5
    if magnitude > 0:
        vector = [v / magnitude for v in vector]

    return vector


def embed_text_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.

    Behavior depends on FEATURE_SIM flag:
    - If False: Returns deterministic hash-based vectors (stub)
    - If True: Would call real embedding model (placeholder for now)

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors, one per input text

    Example:
        >>> vectors = embed_text_batch(["Hello world", "Goodbye"])
        >>> len(vectors)
        2
        >>> len(vectors[0])
        768
    """
    if not texts:
        return []

    if settings.FEATURE_SIM:
        # Placeholder for real embedding implementation
        # TODO: Integrate with OpenAI embeddings or sentence-transformers
        # For now, fall back to stub even if flag is true
        return [_hash_to_vector(text) for text in texts]
    else:
        # Use deterministic stub embeddings
        return [_hash_to_vector(text) for text in texts]


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text.

    Convenience wrapper around embed_text_batch for single inputs.

    Args:
        text: Text string to embed

    Returns:
        Embedding vector as list of floats

    Example:
        >>> vector = embed_text("Hello world")
        >>> len(vector)
        768
    """
    return embed_text_batch([text])[0]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score in range [-1, 1]
        (1 = identical, 0 = orthogonal, -1 = opposite)

    Example:
        >>> v1 = [1.0, 0.0, 0.0]
        >>> v2 = [1.0, 0.0, 0.0]
        >>> cosine_similarity(v1, v2)
        1.0
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(v ** 2 for v in vec1) ** 0.5
    magnitude2 = sum(v ** 2 for v in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
