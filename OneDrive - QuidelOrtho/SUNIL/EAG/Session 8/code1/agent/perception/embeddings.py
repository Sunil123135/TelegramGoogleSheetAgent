"""
Embedding generation using Nomic embeddings with L2 normalization.
"""

import os
import sys
import warnings

# Suppress NumPy/PyTorch compatibility warnings BEFORE any imports
warnings.filterwarnings("ignore", category=UserWarning, message=".*NumPy.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*_ARRAY_API.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Handle SSL certificate issues BEFORE importing anything that uses SSL
# This must be done before importing sentence_transformers or huggingface libraries
if os.environ.get("DISABLE_SSL_VERIFY", "").lower() == "true":
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

import numpy as np
from typing import List, Optional

# Suppress warnings during sentence_transformers import (NumPy compatibility, etc.)
# Skip sentence_transformers entirely if torch isn't properly installed
SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    import torch
    if not hasattr(torch, '_C'):
        raise ImportError("PyTorch C extensions not available")
    # Only attempt sentence_transformers if torch is working
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Suppress all warnings during import
        from sentence_transformers import SentenceTransformer
        SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, Exception) as e:
    # Embeddings disabled - agent will run in minimal mode
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Silently disable for common issues; only warn for unexpected errors
    error_str = str(e)
    lowered = error_str.lower()
    common_issues = (
        "numpy" in lowered
        or "_array_api" in lowered
        or "huggingface" in lowered
        or "transformers" in lowered
        or "dependency_versions_check" in lowered
        or "pytorch" in lowered
        or "torch" in lowered
        or "c extensions" in lowered
        or "long path" in lowered
    )
    if not common_issues:
        print(f"Warning: sentence_transformers not available: {error_str[:100]}")
        print("  Embeddings will be disabled.")

from ..models import Segment, EmbeddingRecord


class EmbeddingGenerator:
    """Generates L2-normalized embeddings for text segments."""
    
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model = None
        self.dimension = 768  # Default dimension for nomic-embed-text-v1.5
        self.model_name = model_name
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Warning: sentence_transformers not available. Embeddings disabled.")
            return
        
        try:
            # Try to load the model with timeout handling
            self.model = SentenceTransformer(
                model_name, 
                trust_remote_code=True,
                device='cpu'  # Use CPU to avoid GPU/ML issues
            )
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            # If model loading fails (SSL error, network issue, etc.), set to None
            # The agent will work in minimal mode without embeddings
            error_msg = str(e)
            
            # Check if it's an SSL/certificate error
            is_ssl_error = (
                "SSL" in error_msg or 
                "certificate" in error_msg.lower() or
                "CERTIFICATE_VERIFY_FAILED" in error_msg or
                "SSLError" in str(type(e).__name__)
            )
            
            if is_ssl_error:
                print(f"Warning: SSL certificate error when loading embedding model {model_name}")
                print("  Agent will run in minimal mode without embeddings.")
                print("  To fix SSL issues:")
                print("    1. Fix SSL certificates (recommended)")
                print("    2. Set DISABLE_SSL_VERIFY=true (not recommended for production)")
            else:
                print(f"Warning: Could not load embedding model {model_name}")
                print(f"  Error: {error_msg[:150]}...")  # Truncate long error messages
                print("  Agent will run in minimal mode without embeddings.")
            
            self.model = None
    
    def embed_segment(self, segment: Segment) -> EmbeddingRecord:
        """
        Generate embedding for a single segment.
        
        Args:
            segment: Text segment to embed
            
        Returns:
            Embedding record with L2-normalized vector
        """
        if self.model is None:
            # Return a zero vector if model not available
            embedding = np.zeros(self.dimension)
        else:
            # Generate embedding
            embedding = self.model.encode(segment.text, convert_to_numpy=True)
        
        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return EmbeddingRecord(
            doc_id=segment.doc_id,
            segment_id=segment.segment_id,
            vector=embedding.tolist(),
            meta={
                "topic_label": segment.topic_label,
                "word_range": f"{segment.start_word}-{segment.end_word}",
                "has_images": len(segment.images) > 0
            }
        )
    
    def embed_segments(self, segments: List[Segment]) -> List[EmbeddingRecord]:
        """
        Batch embed multiple segments efficiently.
        
        Args:
            segments: List of segments to embed
            
        Returns:
            List of embedding records
        """
        if not segments:
            return []
        
        if self.model is None:
            # Return zero vectors if model not available
            embeddings = np.zeros((len(segments), self.dimension))
        else:
            # Extract texts
            texts = [seg.text for seg in segments]
            
            # Batch encode
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        
        # L2 normalize batch
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        
        # Create records
        records = []
        for segment, embedding in zip(segments, embeddings):
            record = EmbeddingRecord(
                doc_id=segment.doc_id,
                segment_id=segment.segment_id,
                vector=embedding.tolist(),
                meta={
                    "topic_label": segment.topic_label,
                    "word_range": f"{segment.start_word}-{segment.end_word}",
                    "has_images": len(segment.images) > 0
                }
            )
            records.append(record)
        
        return records
    
    def embed_query(self, query_text: str) -> np.ndarray:
        """
        Generate L2-normalized embedding for a query.
        
        Args:
            query_text: Query string
            
        Returns:
            L2-normalized embedding vector
        """
        if self.model is None:
            # Return a zero vector if model not available
            embedding = np.zeros(self.dimension)
        else:
            embedding = self.model.encode(query_text, convert_to_numpy=True)
        
        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding

