"""
Pydantic models for data contracts across all layers.
Provides type safety and validation for the agent system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class SourceKind(str, Enum):
    """Types of source documents that can be ingested."""
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    OTHER = "other"


class SourceDoc(BaseModel):
    """Represents a source document before processing."""
    doc_id: str = Field(..., description="Unique identifier for the document")
    uri: str = Field(..., description="URI or path to the source")
    kind: SourceKind = Field(..., description="Type of document")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the source")
    timestamp: datetime = Field(default_factory=datetime.now)


class Segment(BaseModel):
    """Represents a semantically chunked segment of a document."""
    doc_id: str = Field(..., description="Parent document ID")
    segment_id: str = Field(..., description="Unique segment identifier")
    text: str = Field(..., description="Text content of the segment")
    start_word: int = Field(..., description="Starting word index in original doc")
    end_word: int = Field(..., description="Ending word index in original doc")
    topic_label: Optional[str] = Field(None, description="Detected topic label")
    images: List[str] = Field(default_factory=list, description="Image references in this segment")
    meta: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingRecord(BaseModel):
    """Represents a segment with its vector embedding."""
    doc_id: str
    segment_id: str
    vector: List[float] = Field(..., description="L2-normalized embedding vector")
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ImageCaption(BaseModel):
    """Represents a generated caption for an image."""
    image_ref: str = Field(..., description="Image URL or path")
    alt_text: str = Field(..., description="Generated alt text")
    model: str = Field(default="gemma3:12b")
    confidence: Optional[float] = None


class ToolRequest(BaseModel):
    """Represents a request to execute a tool via MCP."""
    name: str = Field(..., description="Tool name (format: server.tool_name)")
    args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    depends_on: List[str] = Field(default_factory=list, description="IDs of prerequisite tool requests")
    request_id: str = Field(..., description="Unique request identifier")


class ToolResult(BaseModel):
    """Result from executing a tool."""
    request_id: str
    name: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PlanStep(BaseModel):
    """Single step in an execution plan."""
    step_id: str
    tool: str = Field(..., description="Tool name to execute")
    args: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list, description="Step IDs this depends on")
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[ToolResult] = None
    description: str = Field(..., description="Human-readable step description")


class ExecutionPlan(BaseModel):
    """Complete execution plan for a multi-step task."""
    plan_id: str
    goal: str = Field(..., description="High-level goal description")
    steps: List[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"


class MemoryEntry(BaseModel):
    """Entry in the agent's scratchpad/long-term memory."""
    entry_id: str
    conversation_id: str
    content: str
    entry_type: Literal["user_message", "agent_response", "tool_result", "note"] = "note"
    timestamp: datetime = Field(default_factory=datetime.now)
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorkingMemory(BaseModel):
    """Short-term working memory for the agent (rolling window)."""
    conversation_id: str
    messages: List[MemoryEntry] = Field(default_factory=list)
    window_size: int = Field(default=10, description="Maximum messages to retain")
    blackboard: Dict[str, Any] = Field(default_factory=dict, description="Shared state between tools")
    
    def add_message(self, entry: MemoryEntry):
        """Add a message and maintain window size."""
        self.messages.append(entry)
        if len(self.messages) > self.window_size:
            self.messages = self.messages[-self.window_size:]


class RetrievalQuery(BaseModel):
    """Query for semantic search in FAISS."""
    query_text: str
    top_k: int = Field(default=5)
    filters: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None


class RetrievalResult(BaseModel):
    """Result from semantic search."""
    segment: Segment
    score: float = Field(..., description="Similarity score")
    embedding_record: Optional[EmbeddingRecord] = None


class AgentState(BaseModel):
    """Current state of the agent."""
    conversation_id: str
    current_goal: Optional[str] = None
    active_plan: Optional[ExecutionPlan] = None
    working_memory: WorkingMemory
    last_activity: datetime = Field(default_factory=datetime.now)
    status: Literal["idle", "processing", "waiting", "error"] = "idle"

