# Architecture Deep Dive

Comprehensive overview of the Cursor Agent architecture.

## System Overview

The Cursor Agent implements a **four-layer cognitive architecture** inspired by AI agent design patterns and production systems:

```
┌──────────────────────────────────────────────────────────────────┐
│                       AGENT ORCHESTRATOR                         │
│  • Conversation State Management                                 │
│  • Cross-layer Coordination                                      │
│  • Error Handling & Recovery                                     │
└──────────────────────────────────────────────────────────────────┘
         ↓                ↓                ↓                ↓
    PERCEPTION         MEMORY          DECISION          ACTION
```

---

## Layer 1: Perception

**Purpose**: Transform raw inputs into structured, searchable knowledge.

### Components

#### 1. Document Ingestion (`agent/perception/ingestion.py`)

**Responsibility**: Convert any document type to clean Markdown.

**Supported Formats**:
- HTML/Web pages → Trafilatura → Markdown
- PDF → MuPDF4LLM → Markdown + images
- Images → Gemma → alt-text description
- Text → Direct ingestion
- Other → Convert to PDF → MuPDF4LLM

**Key Design Decisions**:
- Markdown as universal intermediate format
- Preserve tables and images
- Generate unique document IDs (SHA256 hash)
- Metadata tracking (URI, type, timestamp)

#### 2. Semantic Chunking (`agent/perception/chunking.py`)

**Responsibility**: Split documents into semantically coherent segments.

**Algorithm**: Second-Topic Rule

```python
def chunk_with_second_topic_rule(text, chunk_size=512):
    """
    1. Split text into initial blocks (512 words each)
    2. For each block:
       a. Ask LLM: "Does this contain TWO topics?"
       b. If yes:
          - Finalize FIRST topic as segment
          - Carry SECOND topic to next block
       c. If no:
          - Finalize entire block
    3. Recursively process with carry-over
    """
```

**Why This Works**:
- Prevents mid-topic cuts
- Maintains narrative coherence
- LLM detects subtle topic shifts
- Adaptive to content structure

**Example**:

```
Block 1 (512 words):
"Python is a programming language... [TOPIC 1: Python]
 Rust is gaining popularity... [TOPIC 2: Rust]"

→ Finalize: "Python is a programming language..."
→ Carry: "Rust is gaining popularity..."

Block 2 (512 words):
"Rust is gaining popularity... [continued from carry]
 JavaScript frameworks... [TOPIC 2: JavaScript]"

→ Full Block: "Rust is gaining popularity... JavaScript frameworks..."
```

#### 3. Embedding Generation (`agent/perception/embeddings.py`)

**Responsibility**: Convert text to vector embeddings.

**Model**: Nomic Embed Text v1.5
- Dimension: 768
- L2-normalized for cosine similarity
- Efficient batch encoding

**Process**:
```python
text → Nomic Encoder → vector [768] → L2 normalize → FAISS
```

**Why Nomic**:
- High quality for semantic search
- Efficient inference
- Good balance of size/performance

---

## Layer 2: Memory

**Purpose**: Store, retrieve, and manage knowledge and context.

### Three-Tier Memory System

```
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│ Working Memory  │  │   Scratchpad     │  │   Vector Store      │
│  (Short-term)   │  │  (Long-term)     │  │    (Semantic)       │
├─────────────────┤  ├──────────────────┤  ├─────────────────────┤
│ • Rolling       │  │ • JSONL append   │  │ • FAISS index       │
│   window (10)   │  │ • All messages   │  │ • L2 distance       │
│ • Blackboard    │  │ • Searchable     │  │ • Metadata filters  │
│ • In-memory     │  │ • Persistent     │  │ • Top-k retrieval   │
└─────────────────┘  └──────────────────┘  └─────────────────────┘
    Latency: 0ms         Latency: 1-5ms        Latency: 5-50ms
```

### Components

#### 1. FAISS Vector Store (`agent/memory/vector_store.py`)

**Index Type**: `IndexFlatL2` (exact search)

**Why L2 on Normalized Vectors**:
```
Cosine similarity = 1 - (L2_distance / 2)

For normalized vectors:
  L2(a, b)² = ||a||² + ||b||² - 2⟨a, b⟩
            = 1 + 1 - 2⟨a, b⟩
            = 2(1 - cosine_similarity)
```

**Operations**:
- `add_embeddings()`: Batch insert with metadata
- `search()`: Semantic similarity search
- `get_segment_by_id()`: Direct retrieval
- `save()`/`load()`: Persistence

**Metadata Schema**:
```python
{
    "doc_id": "abc123",
    "segment_id": "abc123_seg_5",
    "text": "Full segment text...",
    "topic_label": "Introduction to Rust",
    "images": ["image1.png"],
    "word_range": "2048-2560"
}
```

#### 2. Memory Scratchpad (`agent/memory/scratchpad.py`)

**Format**: JSON Lines (JSONL)

**Entry Types**:
- `user_message`: User inputs
- `agent_response`: Agent outputs
- `tool_result`: Tool execution logs
- `note`: System notes

**Example Entry**:
```json
{
  "entry_id": "abc123",
  "conversation_id": "conv-001",
  "content": "Created Google Sheet: 1abc...xyz",
  "entry_type": "tool_result",
  "timestamp": "2025-11-02T10:30:00Z",
  "meta": {"tool": "google_sheets_upsert"}
}
```

**Operations**:
- `append()`: Add single entry
- `append_batch()`: Bulk insert
- `get_by_conversation()`: Filter by ID
- `search_content()`: Keyword search

#### 3. Working Memory (`agent/memory/working_memory.py`)

**Design**: Rolling window + blackboard

**Rolling Window**:
```python
messages = [
    MemoryEntry(...),  # Oldest
    MemoryEntry(...),
    MemoryEntry(...),  # Newest
]

# Add new message
messages.append(new_entry)
if len(messages) > window_size:
    messages = messages[-window_size:]  # Keep recent
```

**Blackboard Pattern**:
```python
blackboard = {
    # Tool outputs
    "sheet_url": "https://docs.google.com/...",
    "screenshot_path": "./data/screenshots/...",
    
    # Step-specific state
    "step_step1": {"markdown": "...", "rows": [...]},
    
    # Conversation state
    "user_preferences": {"timezone": "UTC"},
}
```

**Why Blackboard**:
- Shared state across tools
- Avoid explicit parameter passing
- Semantic keys for easy access
- Automatic cleanup per conversation

---

## Layer 3: Decision

**Purpose**: Plan multi-step tasks and select appropriate tools.

### Components

#### 1. Task Planner (`agent/decision/planner.py`)

**Input**: Natural language goal + context

**Output**: Execution plan with dependency graph

**Algorithm**:
```
1. Analyze goal with LLM (Gemini)
2. Break down into atomic steps
3. Assign tools to each step
4. Identify dependencies
5. Create ExecutionPlan
```

**Example Plan**:
```python
ExecutionPlan(
    plan_id="plan-001",
    goal="Find F1 standings and email them",
    steps=[
        PlanStep(step_id="step1", tool="extract_webpage", depends_on=[]),
        PlanStep(step_id="step2", tool="google_sheets_upsert", depends_on=["step1"]),
        PlanStep(step_id="step3", tool="gmail_send", depends_on=["step2"]),
    ]
)
```

**Dependency Resolution**:
```python
# Topological sort
pending = [step1, step2, step3, step4]
completed = []

while pending:
    # Find steps with satisfied dependencies
    executable = [s for s in pending if all(d in completed for d in s.depends_on)]
    
    # Execute in parallel
    for step in executable:
        await execute(step)
        completed.append(step.step_id)
    
    pending = [s for s in pending if s not in executable]
```

#### 2. Tool Selector (`agent/decision/tool_selector.py`)

**Responsibility**: Resolve placeholders and validate tool requests.

**Placeholder Types**:

| Placeholder | Example | Resolved To |
|------------|---------|-------------|
| Blackboard | `{blackboard.sheet_url}` | `"https://docs.google.com/..."` |
| Step Output | `{step1.rows}` | `[["Header"], ["Data"]]` |
| Environment | `{env.SELF_EMAIL}` | `"user@example.com"` |

**Resolution Algorithm**:
```python
def resolve(placeholder, blackboard, step_results):
    parts = placeholder.split(".")
    
    if parts[0] == "blackboard":
        return blackboard[parts[1]]
    elif parts[0] in step_results:
        return step_results[parts[0]][parts[1]]
    elif parts[0] == "env":
        return os.environ[parts[1]]
```

**Validation**:
```python
required_args = {
    "extract_webpage": ["url"],
    "google_sheets_upsert": ["spreadsheet_title", "sheet_name", "rows"],
    ...
}

def validate(tool_request):
    for arg in required_args[tool_request.name]:
        if arg not in tool_request.args:
            raise ValidationError(f"Missing {arg}")
        
        if "{" in str(tool_request.args[arg]):
            raise ValidationError(f"Unresolved placeholder in {arg}")
```

---

## Layer 4: Action

**Purpose**: Execute tools via MCP and update system state.

### Components

#### 1. Tool Executor (`agent/action/executor.py`)

**Responsibility**: Orchestrate tool execution with error handling.

**Execution Flow**:
```
1. Receive ExecutionPlan
2. For each step (in dependency order):
   a. Resolve arguments (via ToolSelector)
   b. Validate tool request
   c. Execute tool (async)
   d. Update blackboard with outputs
   e. Log to memory
3. Return success/failure + final blackboard
```

**Parallel Execution**:
```python
# Find independent steps
executable = [s for s in pending if deps_satisfied(s)]

# Execute in parallel
tasks = [execute_tool(step) for step in executable]
results = await asyncio.gather(*tasks)
```

**Blackboard Update Strategy**:
```python
# Semantic key mapping
mappings = {
    "google_sheets_upsert": {
        "spreadsheet_id": "spreadsheet_id",  # Direct copy
        "sheet_url": "sheet_url",
    },
    "screenshot_url": {
        "path": "screenshot_path",  # Rename for clarity
    }
}

for output_key, blackboard_key in mappings[tool].items():
    if output_key in result:
        blackboard[blackboard_key] = result[output_key]
```

#### 2. MCP Tool Handlers

**Pattern**: One handler per tool

**Example Handler**:
```python
async def _extract_webpage(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract webpage to markdown.
    
    In production: Call MCP stdio server
    For development: Direct library call
    """
    # Option 1: MCP call (production)
    # result = await mcp_client.call_tool("extract_webpage", args)
    
    # Option 2: Direct call (development/testing)
    ingestion = DocumentIngestion()
    doc, markdown = ingestion.ingest_document(args["url"])
    
    return {
        "markdown": markdown,
        "doc_id": doc.doc_id,
        "rows": parse_table(markdown)
    }
```

**Why This Design**:
- Easy to swap MCP vs direct calls
- Testable without MCP infrastructure
- Clear interface boundaries
- Type-safe with Pydantic

---

## MCP Integration

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cursor / Agent                           │
└─────────────────────────────────────────────────────────────┘
                     │ (stdio)
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 │ Trafilatura │ │   Google    │ │  Telegram   │
 │    Server   │ │   Sheets    │ │   Server    │
 │             │ │   Server    │ │             │
 └─────────────┘ └─────────────┘ └─────────────┘
```

### MCP Protocol

**Tool List Request**:
```json
{
  "method": "tools/list",
  "params": {}
}
```

**Tool List Response**:
```json
{
  "tools": [
    {
      "name": "fetch_markdown",
      "description": "Fetch web page and convert to Markdown",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": {"type": "string"}
        },
        "required": ["url"]
      }
    }
  ]
}
```

**Tool Call Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch_markdown",
    "arguments": {
      "url": "https://example.com"
    }
  }
}
```

**Tool Call Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"markdown\": \"# Example\\n...\"}"
    }
  ]
}
```

---

## Agent Orchestrator

**Purpose**: Coordinate all layers and manage conversation state.

### Key Responsibilities

1. **State Management**
   ```python
   states: Dict[conversation_id, AgentState] = {
       "conv-001": AgentState(
           conversation_id="conv-001",
           current_goal="Find F1 standings",
           active_plan=ExecutionPlan(...),
           working_memory=WorkingMemory(...),
           status="processing"
       )
   }
   ```

2. **Message Processing Loop**
   ```
   User Message
       ↓
   Add to Memory
       ↓
   Retrieve Context (FAISS)
       ↓
   Create Plan (Decision)
       ↓
   Execute Plan (Action)
       ↓
   Update Memory
       ↓
   Generate Response
   ```

3. **Error Handling**
   ```python
   try:
       success, blackboard = await executor.execute_plan(plan)
       if not success:
           # Attempt recovery
           refined_plan = planner.refine_plan(plan, error_feedback)
           success, blackboard = await executor.execute_plan(refined_plan)
   except Exception as e:
       # Log to scratchpad
       # Return error response
       # Maintain conversation state
   ```

4. **Context Retrieval**
   ```python
   # Combine multiple sources
   recent_messages = working_memory.messages[-3:]
   retrieved_segments = vector_store.search(query, top_k=5)
   scratchpad_entries = scratchpad.get_recent(limit=10)
   
   context = {
       "recent": [m.content for m in recent_messages],
       "semantic": [s.segment.text for s in retrieved_segments],
       "history": [e.content for e in scratchpad_entries]
   }
   ```

---

## Data Flow Example: F1 Workflow

```
User: "Find F1 standings and email them"
   │
   ├──> [Orchestrator] Create conversation state
   │
   ├──> [Memory] Retrieve context
   │      ├─> Working Memory: last 3 messages
   │      ├─> FAISS: semantic search "F1 standings"
   │      └─> Scratchpad: conversation history
   │
   ├──> [Decision] Create plan
   │      └─> Gemini LLM: "Break down into steps"
   │           └─> [step1: extract_webpage, step2: sheets, step3: email]
   │
   ├──> [Action] Execute plan
   │      │
   │      ├─> Step 1: extract_webpage
   │      │     ├─> [Perception] Trafilatura → Markdown
   │      │     ├─> [Perception] Parse table → rows
   │      │     └─> [Memory] Blackboard ← rows
   │      │
   │      ├─> Step 2: google_sheets_upsert
   │      │     ├─> [Decision] Resolve {step1.rows}
   │      │     ├─> [Action] Google Sheets API
   │      │     └─> [Memory] Blackboard ← sheet_url
   │      │
   │      └─> Step 3: gmail_send
   │            ├─> [Decision] Resolve {blackboard.sheet_url}
   │            ├─> [Action] Gmail API
   │            └─> [Memory] Scratchpad ← log
   │
   └──> [Orchestrator] Generate response
         └─> "✓ F1 standings sent to email"
```

---

## Design Principles

### 1. Separation of Concerns
- Each layer has clear responsibilities
- Minimal coupling between layers
- Explicit interfaces (Pydantic models)

### 2. Composability
- Tools can be chained arbitrarily
- Plans can be nested/refined
- Memory sources can be combined

### 3. Observability
- All actions logged to scratchpad
- Blackboard tracks inter-tool state
- Clear error propagation

### 4. Extensibility
- Add new tools: implement MCP server
- Add new memory: implement interface
- Add new planner: swap Decision component

### 5. Testability
- Pure functions in Perception
- Mockable MCP servers
- Isolated layer testing

---

## Performance Considerations

### Latency Budget

| Operation | Target | Notes |
|-----------|--------|-------|
| Working Memory Access | <1ms | In-memory dict |
| Scratchpad Read | <10ms | Streaming JSONL |
| FAISS Search | <50ms | Exact search, 10k vectors |
| LLM Planning | 1-3s | Gemini API |
| Tool Execution | 0.5-5s | Varies by tool |

### Optimization Strategies

1. **Parallel Execution**
   - Independent steps run simultaneously
   - Example: share + screenshot in parallel

2. **Batch Embeddings**
   - Encode multiple segments at once
   - 10x faster than sequential

3. **Lazy Loading**
   - Load FAISS index on first search
   - Don't load if not needed

4. **Caching**
   - Cache LLM plans for similar queries
   - Cache embeddings by content hash

---

## Scalability

### Current Limits

- **FAISS**: 100k-1M vectors (single index)
- **Scratchpad**: 10M entries (JSONL streaming)
- **Working Memory**: 10-20 messages (in-memory)

### Scale-Up Strategies

1. **Distributed FAISS**
   - Shard by document ID
   - Parallel search across shards

2. **Database Backend**
   - Replace JSONL with SQLite/PostgreSQL
   - Indexed queries for speed

3. **External Memory**
   - S3 for long-term storage
   - Redis for hot cache

4. **Async Everything**
   - All I/O operations async
   - Concurrent tool execution

---

## Security Model

### Threat Model

1. **Credential Exposure**
   - OAuth tokens on disk
   - MCP server compromise

2. **Data Leakage**
   - Embeddings encode information
   - Scratchpad contains PII

3. **Injection Attacks**
   - Malicious URLs in goals
   - SQL injection in tool args

### Mitigations

1. **Credential Isolation**
   - Separate tokens per API
   - 600 permissions on files
   - Rotate periodically

2. **Sandboxing**
   - MCP servers run in separate processes
   - No shell access from tools

3. **Input Validation**
   - Pydantic models enforce types
   - URL validation before fetch
   - SQL parameterization

4. **Audit Logging**
   - All tool calls logged
   - Timestamps for traceability

---

## Future Enhancements

1. **Streaming Execution**
   - SSE MCP server for real-time updates
   - WebSocket for UI

2. **Multi-Agent Collaboration**
   - Specialized sub-agents
   - Shared memory space

3. **Learning from Feedback**
   - Store successful plans
   - Fine-tune planning model

4. **Advanced Memory**
   - Hierarchical summarization
   - Knowledge graph extraction

---

This architecture provides a solid foundation for building sophisticated agent systems while remaining maintainable and extensible.

