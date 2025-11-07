"""
Short-term working memory (rolling window).
Maintains recent context and shared state (blackboard).
"""

from typing import Dict, Any, Optional, List
from ..models import WorkingMemory, MemoryEntry


class WorkingMemoryManager:
    """Manages short-term working memory with rolling window."""
    
    def __init__(self, window_size: int = 10):
        """
        Initialize working memory manager.
        
        Args:
            window_size: Maximum number of messages to retain
        """
        self.window_size = window_size
        self.memories: Dict[str, WorkingMemory] = {}
    
    def get_memory(self, conversation_id: str) -> WorkingMemory:
        """
        Get or create working memory for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Working memory instance
        """
        if conversation_id not in self.memories:
            self.memories[conversation_id] = WorkingMemory(
                conversation_id=conversation_id,
                window_size=self.window_size
            )
        return self.memories[conversation_id]
    
    def add_message(self, conversation_id: str, entry: MemoryEntry):
        """
        Add a message to working memory.
        
        Args:
            conversation_id: Conversation identifier
            entry: Memory entry to add
        """
        memory = self.get_memory(conversation_id)
        memory.add_message(entry)
    
    def get_recent_context(self, conversation_id: str, n: Optional[int] = None) -> List[MemoryEntry]:
        """
        Get recent messages as context.
        
        Args:
            conversation_id: Conversation identifier
            n: Number of recent messages (defaults to window_size)
            
        Returns:
            List of recent memory entries
        """
        memory = self.get_memory(conversation_id)
        if n is None:
            return memory.messages
        return memory.messages[-n:]
    
    def set_blackboard_value(self, conversation_id: str, key: str, value: Any):
        """
        Set a value in the blackboard (shared state).
        
        Args:
            conversation_id: Conversation identifier
            key: Blackboard key
            value: Value to store
        """
        memory = self.get_memory(conversation_id)
        memory.blackboard[key] = value
    
    def get_blackboard_value(self, conversation_id: str, key: str, default: Any = None) -> Any:
        """
        Get a value from the blackboard.
        
        Args:
            conversation_id: Conversation identifier
            key: Blackboard key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        memory = self.get_memory(conversation_id)
        return memory.blackboard.get(key, default)
    
    def update_blackboard(self, conversation_id: str, updates: Dict[str, Any]):
        """
        Update multiple blackboard values at once.
        
        Args:
            conversation_id: Conversation identifier
            updates: Dictionary of key-value pairs to update
        """
        memory = self.get_memory(conversation_id)
        memory.blackboard.update(updates)
    
    def get_blackboard(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the entire blackboard.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Blackboard dictionary
        """
        memory = self.get_memory(conversation_id)
        return memory.blackboard.copy()
    
    def clear_blackboard(self, conversation_id: str):
        """
        Clear the blackboard for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        memory = self.get_memory(conversation_id)
        memory.blackboard.clear()
    
    def clear_memory(self, conversation_id: str):
        """
        Clear all working memory for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.memories:
            del self.memories[conversation_id]
    
    def get_memory_summary(self, conversation_id: str) -> str:
        """
        Get a text summary of working memory.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Human-readable summary
        """
        memory = self.get_memory(conversation_id)
        
        lines = [f"Working Memory for {conversation_id}:"]
        lines.append(f"  Messages: {len(memory.messages)}/{memory.window_size}")
        lines.append(f"  Blackboard keys: {list(memory.blackboard.keys())}")
        
        if memory.messages:
            lines.append("  Recent messages:")
            for msg in memory.messages[-3:]:
                lines.append(f"    [{msg.entry_type}] {msg.content[:60]}...")
        
        return "\n".join(lines)

