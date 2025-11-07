"""
Semantic chunking with "second-topic" rule.

If a block contains two topics, return only the second topic;
the first topic is finalized and the second topic is prepended to the next block.
"""

import re
from typing import List, Optional, Tuple
from ..models import Segment, SourceDoc
from google import genai


class SemanticChunker:
    """Implements the second-topic rule for semantic chunking."""
    
    def __init__(self, chunk_size: int = 512, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the semantic chunker.
        
        Args:
            chunk_size: Target word count per chunk
            model: Gemini model for topic detection
        """
        self.chunk_size = chunk_size
        self.client = genai.Client()
        self.model = model
    
    def chunk_document(self, doc: SourceDoc, text: str) -> List[Segment]:
        """
        Chunk a document using the second-topic rule.
        
        Args:
            doc: Source document metadata
            text: Full text content to chunk
            
        Returns:
            List of semantically coherent segments
        """
        # Split into initial word-based blocks
        words = text.split()
        initial_blocks = self._create_initial_blocks(words)
        
        # Apply second-topic rule
        segments = []
        carry_over = ""
        word_offset = 0
        
        for i, block in enumerate(initial_blocks):
            # Prepend carry-over from previous block
            full_block = carry_over + " " + block if carry_over else block
            
            # Detect if there's a second topic
            second_topic_text = self._detect_second_topic(full_block)
            
            if second_topic_text and second_topic_text.strip():
                # Extract finalized first topic
                first_topic = full_block.replace(second_topic_text, "").strip()
                
                if first_topic:
                    # Create segment for first topic
                    first_words = first_topic.split()
                    segment = Segment(
                        doc_id=doc.doc_id,
                        segment_id=f"{doc.doc_id}_seg_{len(segments)}",
                        text=first_topic,
                        start_word=word_offset,
                        end_word=word_offset + len(first_words),
                        topic_label=self._extract_topic_label(first_topic),
                        images=self._extract_image_refs(first_topic),
                        meta={"block_index": i}
                    )
                    segments.append(segment)
                    word_offset += len(first_words)
                
                # Carry second topic to next block
                carry_over = second_topic_text.strip()
            else:
                # No second topic; finalize entire block
                full_words = full_block.split()
                segment = Segment(
                    doc_id=doc.doc_id,
                    segment_id=f"{doc.doc_id}_seg_{len(segments)}",
                    text=full_block,
                    start_word=word_offset,
                    end_word=word_offset + len(full_words),
                    topic_label=self._extract_topic_label(full_block),
                    images=self._extract_image_refs(full_block),
                    meta={"block_index": i}
                )
                segments.append(segment)
                word_offset += len(full_words)
                carry_over = ""
        
        # Handle any remaining carry-over
        if carry_over.strip():
            carry_words = carry_over.split()
            segment = Segment(
                doc_id=doc.doc_id,
                segment_id=f"{doc.doc_id}_seg_{len(segments)}",
                text=carry_over,
                start_word=word_offset,
                end_word=word_offset + len(carry_words),
                topic_label=self._extract_topic_label(carry_over),
                images=self._extract_image_refs(carry_over),
                meta={"block_index": len(initial_blocks)}
            )
            segments.append(segment)
        
        return segments
    
    def _create_initial_blocks(self, words: List[str]) -> List[str]:
        """Split words into initial blocks of target size."""
        blocks = []
        for i in range(0, len(words), self.chunk_size):
            block = " ".join(words[i:i + self.chunk_size])
            blocks.append(block)
        return blocks
    
    def _detect_second_topic(self, block: str) -> Optional[str]:
        """
        Use Gemini to detect if there's a second topic in the block.
        
        Returns:
            The text of the second topic, or None if only one topic exists.
        """
        prompt = f"""Analyze the following text block. If it contains TWO distinct topics, return ONLY the text of the SECOND topic. If there's only one topic, return an empty string.

Text block:
{block}

Instructions:
- If you detect a clear topic shift (new subject, different focus), extract ONLY the second topic text
- Return the exact text from where the second topic begins
- If only one topic exists, return: ""
- Do not add explanations, just return the text or empty string

Second topic text:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = response.text.strip()
            
            # Clean up common LLM response patterns
            if result.lower() in ["", '""', "none", "n/a", "no second topic"]:
                return None
            
            return result
        except Exception as e:
            print(f"Warning: Topic detection failed: {e}")
            return None
    
    def _extract_topic_label(self, text: str) -> Optional[str]:
        """Extract a brief topic label from text (first sentence or heading)."""
        # Try to find a heading (markdown or HTML)
        heading_match = re.search(r'^#+\s+(.+)$', text, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()
        
        heading_match = re.search(r'<h[1-6]>(.+?)</h[1-6]>', text, re.IGNORECASE)
        if heading_match:
            return heading_match.group(1).strip()
        
        # Use first sentence as topic
        sentences = re.split(r'[.!?]\s+', text)
        if sentences:
            return sentences[0][:100]  # First 100 chars of first sentence
        
        return None
    
    def _extract_image_refs(self, text: str) -> List[str]:
        """Extract image references from markdown or HTML."""
        images = []
        
        # Markdown images: ![alt](url)
        md_images = re.findall(r'!\[.*?\]\((.*?)\)', text)
        images.extend(md_images)
        
        # HTML images: <img src="url">
        html_images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE)
        images.extend(html_images)
        
        return images

