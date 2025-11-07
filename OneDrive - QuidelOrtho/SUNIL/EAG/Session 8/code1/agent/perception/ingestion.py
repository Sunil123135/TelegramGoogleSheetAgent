"""
Document ingestion and conversion to Markdown.

Handles web pages (Trafilatura), PDFs (MuPDF4LLM), images (Gemma captioning),
and other formats. Funnels everything to clean Markdown.
"""

import os
import re
from typing import Tuple, List
from pathlib import Path
import hashlib
from ..models import SourceDoc, SourceKind, ImageCaption


class DocumentIngestion:
    """Handles ingestion and conversion of various document types."""
    
    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.temp_dir = Path("./data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def ingest_document(self, uri: str, kind: SourceKind = None) -> Tuple[SourceDoc, str]:
        """
        Ingest a document and convert to Markdown.
        
        Args:
            uri: URL or file path
            kind: Document type (auto-detected if None)
            
        Returns:
            Tuple of (SourceDoc metadata, Markdown text)
        """
        if kind is None:
            kind = self._detect_kind(uri)
        
        # Generate document ID
        doc_id = self._generate_doc_id(uri)
        
        # Create source doc
        source_doc = SourceDoc(
            doc_id=doc_id,
            uri=uri,
            kind=kind,
            meta={"original_uri": uri}
        )
        
        # Convert to markdown based on type
        if kind == SourceKind.HTML:
            markdown = self._ingest_html(uri)
        elif kind == SourceKind.PDF:
            markdown = self._ingest_pdf(uri)
        elif kind == SourceKind.IMAGE:
            markdown = self._ingest_image(uri)
        elif kind == SourceKind.TEXT:
            markdown = self._ingest_text(uri)
        else:
            # Try to convert other formats to PDF first, then use MuPDF
            markdown = self._ingest_other(uri)
        
        return source_doc, markdown
    
    def _detect_kind(self, uri: str) -> SourceKind:
        """Auto-detect document type from URI."""
        uri_lower = uri.lower()
        
        if uri.startswith("http://") or uri.startswith("https://"):
            if any(ext in uri_lower for ext in [".pdf"]):
                return SourceKind.PDF
            elif any(ext in uri_lower for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                return SourceKind.IMAGE
            else:
                return SourceKind.HTML
        
        # File path
        path = Path(uri)
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            return SourceKind.PDF
        elif suffix in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]:
            return SourceKind.IMAGE
        elif suffix in [".txt", ".md", ".markdown"]:
            return SourceKind.TEXT
        elif suffix in [".html", ".htm"]:
            return SourceKind.HTML
        else:
            return SourceKind.OTHER
    
    def _generate_doc_id(self, uri: str) -> str:
        """Generate a unique document ID from URI."""
        return hashlib.sha256(uri.encode()).hexdigest()[:16]
    
    def _ingest_html(self, uri: str) -> str:
        """
        Ingest HTML/web page using Trafilatura.
        
        Note: In production, this would call the MCP trafilatura-stdio server.
        For now, using direct library call.
        """
        try:
            import trafilatura
            
            if uri.startswith("http"):
                downloaded = trafilatura.fetch_url(uri)
            else:
                with open(uri, 'r', encoding='utf-8') as f:
                    downloaded = f.read()
            
            # Extract with table and image preservation
            markdown = trafilatura.extract(
                downloaded,
                output_format="markdown",
                include_tables=True,
                include_images=True,
                include_links=True
            )
            
            return markdown or ""
        except Exception as e:
            print(f"Error ingesting HTML: {e}")
            return f"Error: Could not ingest {uri}"
    
    def _ingest_pdf(self, uri: str) -> str:
        """
        Ingest PDF using MuPDF4LLM.
        
        Note: In production, this would call the MCP mupdf4llm-stdio server.
        """
        try:
            import pymupdf4llm
            
            # Download if URL
            if uri.startswith("http"):
                import requests
                response = requests.get(uri)
                temp_path = self.temp_dir / f"temp_{self._generate_doc_id(uri)}.pdf"
                temp_path.write_bytes(response.content)
                pdf_path = str(temp_path)
            else:
                pdf_path = uri
            
            # Convert to markdown
            md_text = pymupdf4llm.to_markdown(pdf_path)
            
            return md_text
        except Exception as e:
            print(f"Error ingesting PDF: {e}")
            return f"Error: Could not ingest {uri}"
    
    def _ingest_image(self, uri: str) -> str:
        """
        Ingest image by generating caption with Gemma.
        
        Note: In production, this would call the MCP gemma-caption-stdio server.
        """
        try:
            # For now, return a placeholder
            # In production, call MCP server or use Gemma directly
            caption = f"[Image: {os.path.basename(uri)}]"
            markdown = f"![{caption}]({uri})\n\n{caption}"
            return markdown
        except Exception as e:
            print(f"Error ingesting image: {e}")
            return f"Error: Could not ingest {uri}"
    
    def _ingest_text(self, uri: str) -> str:
        """Ingest plain text file."""
        try:
            if uri.startswith("http"):
                import requests
                response = requests.get(uri)
                return response.text
            else:
                with open(uri, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error ingesting text: {e}")
            return f"Error: Could not ingest {uri}"
    
    def _ingest_other(self, uri: str) -> str:
        """Handle other formats (attempt conversion to PDF first)."""
        # Placeholder - in production, use a file converter
        return f"Unsupported format: {uri}"
    
    def enhance_images_with_captions(self, markdown: str, captions: List[ImageCaption]) -> str:
        """
        Replace image references with captioned versions.
        
        Args:
            markdown: Original markdown with image refs
            captions: Generated captions for images
            
        Returns:
            Enhanced markdown with alt text
        """
        enhanced = markdown
        
        for caption in captions:
            # Replace markdown images
            pattern = rf'!\[.*?\]\({re.escape(caption.image_ref)}\)'
            replacement = f'![{caption.alt_text}]({caption.image_ref})'
            enhanced = re.sub(pattern, replacement, enhanced)
            
            # Replace HTML images
            pattern = rf'<img[^>]+src=["\']({re.escape(caption.image_ref)})["\'][^>]*>'
            replacement = f'<img src="{caption.image_ref}" alt="{caption.alt_text}">'
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        return enhanced

