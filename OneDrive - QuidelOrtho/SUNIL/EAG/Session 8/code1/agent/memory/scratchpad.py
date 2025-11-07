"""
Long-term memory scratchpad stored as JSONL.
Persists conversation history, tool results, and notes.
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..models import MemoryEntry


class MemoryScratchpad:
    """JSONL-based long-term memory storage."""
    
    def __init__(self, scratchpad_path: str = "./data/memory_scratchpad.jsonl"):
        """
        Initialize memory scratchpad.
        
        Args:
            scratchpad_path: Path to JSONL file
        """
        self.scratchpad_path = Path(scratchpad_path)
        self.scratchpad_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.scratchpad_path.exists():
            self.scratchpad_path.touch()
    
    def append(self, entry: MemoryEntry):
        """
        Append a memory entry to the scratchpad.
        
        Args:
            entry: Memory entry to append
        """
        with open(self.scratchpad_path, 'a', encoding='utf-8') as f:
            # Convert to dict and handle datetime serialization
            entry_dict = entry.model_dump()
            entry_dict['timestamp'] = entry.timestamp.isoformat()
            
            f.write(json.dumps(entry_dict) + '\n')
    
    def append_batch(self, entries: List[MemoryEntry]):
        """Append multiple entries efficiently."""
        with open(self.scratchpad_path, 'a', encoding='utf-8') as f:
            for entry in entries:
                entry_dict = entry.model_dump()
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                f.write(json.dumps(entry_dict) + '\n')
    
    def get_by_conversation(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[MemoryEntry]:
        """
        Retrieve entries for a specific conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of entries (most recent if limited)
            
        Returns:
            List of memory entries
        """
        entries = []
        
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    if data.get('conversation_id') == conversation_id:
                        # Parse timestamp
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                        entry = MemoryEntry(**data)
                        entries.append(entry)
                except Exception as e:
                    print(f"Warning: Failed to parse scratchpad entry: {e}")
        
        # Sort by timestamp (newest last)
        entries.sort(key=lambda e: e.timestamp)
        
        # Apply limit (most recent)
        if limit and len(entries) > limit:
            entries = entries[-limit:]
        
        return entries
    
    def get_recent(self, limit: int = 100) -> List[MemoryEntry]:
        """
        Get most recent entries across all conversations.
        
        Args:
            limit: Number of recent entries to return
            
        Returns:
            List of memory entries
        """
        entries = []
        
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    entry = MemoryEntry(**data)
                    entries.append(entry)
                except Exception as e:
                    print(f"Warning: Failed to parse scratchpad entry: {e}")
        
        # Sort by timestamp and take most recent
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]
    
    def search_content(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Simple keyword search in scratchpad content.
        
        Args:
            query: Search query
            conversation_id: Optional conversation filter
            limit: Maximum results
            
        Returns:
            List of matching memory entries
        """
        query_lower = query.lower()
        matches = []
        
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Filter by conversation if specified
                    if conversation_id and data.get('conversation_id') != conversation_id:
                        continue
                    
                    # Check if query appears in content
                    content = data.get('content', '').lower()
                    if query_lower in content:
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                        entry = MemoryEntry(**data)
                        matches.append(entry)
                except Exception as e:
                    print(f"Warning: Failed to parse scratchpad entry: {e}")
        
        # Sort by timestamp (most recent first)
        matches.sort(key=lambda e: e.timestamp, reverse=True)
        return matches[:limit]
    
    def clear_conversation(self, conversation_id: str):
        """
        Remove all entries for a conversation.
        
        Args:
            conversation_id: Conversation to clear
        """
        # Read all entries
        entries = []
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get('conversation_id') != conversation_id:
                        entries.append(line)
                except Exception:
                    entries.append(line)  # Keep unparseable lines
        
        # Rewrite file without the conversation
        with open(self.scratchpad_path, 'w', encoding='utf-8') as f:
            f.writelines(entries)
    
    def get_stats(self) -> dict:
        """Get statistics about the scratchpad."""
        total = 0
        conversations = set()
        entry_types = {}
        
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                total += 1
                try:
                    data = json.loads(line)
                    conversations.add(data.get('conversation_id', 'unknown'))
                    entry_type = data.get('entry_type', 'unknown')
                    entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
                except Exception:
                    pass
        
        return {
            'total_entries': total,
            'unique_conversations': len(conversations),
            'entry_types': entry_types
        }

