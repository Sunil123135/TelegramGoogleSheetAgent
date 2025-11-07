"""
FAISS-based vector store for semantic search.
Stores L2-normalized embeddings with metadata.
"""

import os
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
import faiss
from ..models import EmbeddingRecord, Segment, RetrievalQuery, RetrievalResult


class FAISSVectorStore:
    """FAISS vector store for semantic retrieval."""
    
    def __init__(self, index_path: str = "./data/faiss_index", dimension: int = 768):
        """
        Initialize FAISS vector store.
        
        Args:
            index_path: Path to store/load FAISS index
            dimension: Embedding dimension (768 for Nomic)
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.dimension = dimension
        self.index = None
        self.metadata: Dict[int, Dict[str, Any]] = {}  # idx -> metadata
        self.segment_map: Dict[str, int] = {}  # segment_id -> idx
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or load FAISS index."""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            # Load existing index
            self.index = faiss.read_index(str(index_file))
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.segment_map = data['segment_map']
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            # Create new index (L2 distance, since vectors are normalized, this is cosine similarity)
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index")
    
    def add_embeddings(self, records: List[EmbeddingRecord], segments: List[Segment] = None):
        """
        Add embedding records to the index.
        
        Args:
            records: Embedding records to add
            segments: Optional corresponding segments for richer metadata
        """
        if not records:
            return
        
        # Convert to numpy array
        vectors = np.array([rec.vector for rec in records], dtype=np.float32)
        
        # Get starting index
        start_idx = self.index.ntotal
        
        # Add to FAISS
        self.index.add(vectors)
        
        # Store metadata
        for i, record in enumerate(records):
            idx = start_idx + i
            self.metadata[idx] = {
                'doc_id': record.doc_id,
                'segment_id': record.segment_id,
                'meta': record.meta,
                'timestamp': record.timestamp.isoformat()
            }
            self.segment_map[record.segment_id] = idx
        
        # Add segment data if provided
        if segments:
            for i, segment in enumerate(segments):
                idx = start_idx + i
                if idx in self.metadata:
                    self.metadata[idx].update({
                        'text': segment.text,
                        'topic_label': segment.topic_label,
                        'images': segment.images,
                        'word_range': f"{segment.start_word}-{segment.end_word}"
                    })
        
        print(f"Added {len(records)} embeddings to FAISS index (total: {self.index.ntotal})")
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: L2-normalized query vector
            top_k: Number of results to return
            filters: Optional metadata filters (e.g., {'doc_id': 'abc123'})
            
        Returns:
            List of retrieval results sorted by similarity
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure query is 2D
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Search (L2 distance on normalized vectors = 2 * (1 - cosine_similarity))
        distances, indices = self.index.search(query_vector.astype(np.float32), min(top_k * 2, self.index.ntotal))
        
        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue
            
            metadata = self.metadata.get(int(idx))
            if metadata is None:
                continue
            
            # Apply filters
            if filters and not self._matches_filters(metadata, filters):
                continue
            
            # Convert L2 distance to cosine similarity: sim = 1 - (dist / 2)
            similarity_score = 1.0 - (float(dist) / 2.0)
            
            # Create segment from metadata
            segment = Segment(
                doc_id=metadata['doc_id'],
                segment_id=metadata['segment_id'],
                text=metadata.get('text', ''),
                start_word=int(metadata.get('word_range', '0-0').split('-')[0]),
                end_word=int(metadata.get('word_range', '0-0').split('-')[1]),
                topic_label=metadata.get('topic_label'),
                images=metadata.get('images', []),
                meta=metadata.get('meta', {})
            )
            
            result = RetrievalResult(
                segment=segment,
                score=similarity_score
            )
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches all filters."""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def save(self):
        """Persist index and metadata to disk."""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        faiss.write_index(self.index, str(index_file))
        
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'segment_map': self.segment_map
            }, f)
        
        print(f"Saved FAISS index with {self.index.ntotal} vectors to {self.index_path}")
    
    def get_segment_by_id(self, segment_id: str) -> Optional[Segment]:
        """Retrieve a segment by its ID."""
        idx = self.segment_map.get(segment_id)
        if idx is None:
            return None
        
        metadata = self.metadata.get(idx)
        if metadata is None:
            return None
        
        return Segment(
            doc_id=metadata['doc_id'],
            segment_id=metadata['segment_id'],
            text=metadata.get('text', ''),
            start_word=int(metadata.get('word_range', '0-0').split('-')[0]),
            end_word=int(metadata.get('word_range', '0-0').split('-')[1]),
            topic_label=metadata.get('topic_label'),
            images=metadata.get('images', []),
            meta=metadata.get('meta', {})
        )
    
    def clear(self):
        """Clear the index and metadata."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata.clear()
        self.segment_map.clear()
        print("Cleared FAISS index")

