"""
Agent orchestration loop.

Coordinates Perception, Memory, Decision, and Action layers.
Maintains conversation state and executes multi-step plans.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    AgentState, MemoryEntry, ExecutionPlan, RetrievalQuery,
    SourceDoc, SourceKind
)
from .memory import MemoryScratchpad, WorkingMemoryManager
from .decision import TaskPlanner, ToolSelector
from .action import ToolExecutor


class CursorAgent:
    """
    Main agent orchestrator with 4-layer architecture:
    - Perception: ingestion, chunking, embeddings
    - Memory: FAISS vector store, working memory, scratchpad
    - Decision: planning, tool selection
    - Action: tool execution
    """
    
    def __init__(
        self,
        embedding_model: str = "nomic-ai/nomic-embed-text-v1.5",
        planning_model: str = "gemini-2.0-flash-exp",
        chunk_size: int = 512,
        faiss_index_path: str = "./data/faiss_index",
        scratchpad_path: str = "./data/memory_scratchpad.jsonl"
    ):
        """
        Initialize the Cursor Agent.
        
        Args:
            embedding_model: Model for generating embeddings
            planning_model: Model for planning and reasoning
            chunk_size: Word count for semantic chunks
            faiss_index_path: Path to FAISS index
            scratchpad_path: Path to memory scratchpad
        """
        # Perception + Memory setup (lazy/optional to avoid heavy deps at startup)
        self.ingestion = None
        self.chunker = None
        self.embedder = None
        self.vector_store = None

        try:
            # Delay heavy imports until runtime, and guard failures
            from .perception import DocumentIngestion, SemanticChunker, EmbeddingGenerator
            from .memory import FAISSVectorStore

            self.ingestion = DocumentIngestion()
            self.chunker = SemanticChunker(chunk_size=chunk_size, model=planning_model)
            self.embedder = EmbeddingGenerator(model_name=embedding_model)
            self.vector_store = FAISSVectorStore(index_path=faiss_index_path, dimension=768)
        except Exception as e:
            # Fall back to minimal mode (no embeddings/context retrieval)
            self.ingestion = self.ingestion or None
            self.chunker = self.chunker or None
            self.embedder = None
            self.vector_store = None
            # Minimal scratchpad note will be added when first used
        self.scratchpad = MemoryScratchpad(scratchpad_path=scratchpad_path)
        self.working_memory = WorkingMemoryManager(window_size=10)
        
        # Decision layer
        self.planner = TaskPlanner(model=planning_model)
        self.tool_selector = ToolSelector()
        
        # Action layer
        self.executor = ToolExecutor()
        
        # Agent state
        self.states: Dict[str, AgentState] = {}
    
    def _get_or_create_state(self, conversation_id: str) -> AgentState:
        """Get or create agent state for a conversation."""
        if conversation_id not in self.states:
            working_memory = self.working_memory.get_memory(conversation_id)
            self.states[conversation_id] = AgentState(
                conversation_id=conversation_id,
                working_memory=working_memory,
                status="idle"
            )
        return self.states[conversation_id]
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Process a user message through the agent.
        
        Args:
            user_message: User's input message
            conversation_id: Conversation identifier (generated if None)
            
        Returns:
            Agent's response
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        state = self._get_or_create_state(conversation_id)
        state.status = "processing"
        state.last_activity = datetime.now()
        
        # Add user message to memory
        user_entry = MemoryEntry(
            entry_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            content=user_message,
            entry_type="user_message"
        )
        self.working_memory.add_message(conversation_id, user_entry)
        self.scratchpad.append(user_entry)
        
        # Retrieve relevant context from FAISS
        context = await self._retrieve_context(user_message, conversation_id)
        
        # Extract goal and create plan
        state.current_goal = user_message
        
        context_dict = {
            "conversation_history": [e.content for e in state.working_memory.messages[-3:]],
            "retrieved_context": [c.segment.text[:200] for c in context[:2]]
        }
        
        plan = self.planner.create_plan(user_message, context=context_dict)
        state.active_plan = plan
        
        # Execute plan
        blackboard = self.working_memory.get_blackboard(conversation_id)
        success, blackboard = await self.executor.execute_plan(plan, blackboard)
        
        # Update blackboard
        self.working_memory.update_blackboard(conversation_id, blackboard)
        
        # Generate response
        if success:
            response = self._generate_success_response(plan, blackboard)
        else:
            response = self._generate_error_response(plan)
        
        # Add agent response to memory
        agent_entry = MemoryEntry(
            entry_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            content=response,
            entry_type="agent_response"
        )
        self.working_memory.add_message(conversation_id, agent_entry)
        self.scratchpad.append(agent_entry)
        
        state.status = "idle"
        
        return response
    
    async def _retrieve_context(
        self,
        query: str,
        conversation_id: str,
        top_k: int = 5
    ):
        """Retrieve relevant context from FAISS."""
        if not self.embedder or not self.vector_store:
            return []
        query_vector = self.embedder.embed_query(query)
        results = self.vector_store.search(
            query_vector,
            top_k=top_k,
            filters={"conversation_id": conversation_id} if conversation_id else None
        )
        return results
    
    def _generate_success_response(self, plan: ExecutionPlan, blackboard: Dict[str, Any]) -> str:
        """Generate a response for successful plan execution."""
        lines = [f"✓ Successfully completed: {plan.goal}\n"]
        
        # Extract key outputs from blackboard
        if "sheet_url" in blackboard:
            lines.append(f"📊 Google Sheet: {blackboard['sheet_url']}")
        
        if "share_link" in blackboard:
            lines.append(f"🔗 Share link: {blackboard['share_link']}")
        
        if "email_message_id" in blackboard:
            lines.append(f"📧 Email sent (ID: {blackboard['email_message_id']})")
        
        # Add step summary
        completed_steps = [s for s in plan.steps if s.status == "completed"]
        lines.append(f"\nCompleted {len(completed_steps)}/{len(plan.steps)} steps.")
        
        return "\n".join(lines)
    
    def _generate_error_response(self, plan: ExecutionPlan) -> str:
        """Generate a response for failed plan execution."""
        failed_steps = [s for s in plan.steps if s.status == "failed"]
        
        if failed_steps:
            step = failed_steps[0]
            error = step.result.error if step.result else "Unknown error"
            return f"❌ Failed at step '{step.description}': {error}"
        
        return f"❌ Failed to complete: {plan.goal}"
    
    async def ingest_document(
        self,
        uri: str,
        kind: Optional[SourceKind] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Ingest a document into memory.
        
        Args:
            uri: Document URI (URL or file path)
            kind: Document type (auto-detected if None)
            conversation_id: Associate with a conversation
            
        Returns:
            Document ID
        """
        # Perception: ingest and convert
        if not self.ingestion or not self.chunker or not self.embedder or not self.vector_store:
            # Minimal ingestion disabled when heavy deps unavailable
            raise RuntimeError("Ingestion with embeddings is unavailable in minimal mode.")
        doc, markdown = self.ingestion.ingest_document(uri, kind)
        
        # Perception: semantic chunking
        segments = self.chunker.chunk_document(doc, markdown)
        
        # Perception: generate embeddings
        embedding_records = self.embedder.embed_segments(segments)
        
        # Memory: store in FAISS
        self.vector_store.add_embeddings(embedding_records, segments)
        self.vector_store.save()
        
        # Memory: log to scratchpad
        if conversation_id:
            entry = MemoryEntry(
                entry_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content=f"Ingested document: {uri} (ID: {doc.doc_id}, {len(segments)} segments)",
                entry_type="note"
            )
            self.scratchpad.append(entry)
        
        print(f"✓ Ingested {uri}")
        print(f"  - Document ID: {doc.doc_id}")
        print(f"  - Segments: {len(segments)}")
        print(f"  - Embeddings: {len(embedding_records)}")
        
        return doc.doc_id
    
    async def execute_workflow(
        self,
        goal: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow and return detailed results.
        
        Args:
            goal: Workflow goal
            conversation_id: Conversation identifier
            
        Returns:
            Dict with execution results
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        state = self._get_or_create_state(conversation_id)
        state.current_goal = goal
        
        # Create plan
        plan = self.planner.create_plan(goal)
        state.active_plan = plan
        
        # Execute
        blackboard = {}
        success, blackboard = await self.executor.execute_plan(plan, blackboard)
        
        return {
            "success": success,
            "plan": plan,
            "blackboard": blackboard,
            "conversation_id": conversation_id
        }
    
    def get_memory_summary(self, conversation_id: str) -> str:
        """Get a summary of memory for a conversation."""
        lines = []
        
        # Working memory
        lines.append(self.working_memory.get_memory_summary(conversation_id))
        
        # Scratchpad stats
        entries = self.scratchpad.get_by_conversation(conversation_id, limit=10)
        lines.append(f"\nScratchpad: {len(entries)} recent entries")
        
        # FAISS stats
        lines.append(f"\nVector store: {self.vector_store.index.ntotal} total embeddings")
        
        return "\n".join(lines)
    
    def save_state(self):
        """Persist all memory to disk."""
        self.vector_store.save()
        print("✓ Saved agent state")


if __name__ == "__main__":
    print("❌ Error: Cannot run orchestrator.py directly!")
    print("\n📖 This module uses relative imports and must be run as part of the package.\n")
    print("✅ Correct usage:")
    print("   From project root, run:")
    print("   - python main.py              # Run F1 workflow")
    print("   - python main.py f1           # Run F1 workflow")
    print("   - python main.py interactive  # Interactive mode")
    print("\nFor more info, see: README.md or QUICKSTART.md")