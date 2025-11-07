"""
Multi-step task planner.

Analyzes user intent, breaks down into execution steps, and creates a plan graph.
"""

import uuid
from typing import List, Dict, Any, Optional
try:
    from google import genai  # Optional; planner can run without it
except Exception:  # pragma: no cover
    genai = None
from ..models import ExecutionPlan, PlanStep, ToolRequest


class TaskPlanner:
    """Plans multi-step task execution."""
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the task planner.
        
        Args:
            model: Gemini model for planning
        """
        self.client = None
        self.model = model
        if genai is not None:
            try:
                self.client = genai.Client()
            except Exception:
                self.client = None
        
        # Tool catalog - available tools with descriptions
        self.tool_catalog = {
            "extract_webpage": "Fetch and convert web page to Markdown (trafilatura)",
            "extract_pdf": "Convert PDF to Markdown with images (mupdf4llm)",
            "caption_image": "Generate alt-text caption for an image (gemma)",
            "google_sheets_upsert": "Create or update Google Sheet with data",
            "google_drive_share": "Share a Google Drive file with permissions",
            "gmail_send": "Send email via Gmail with optional attachments",
            "telegram_send": "Send message to Telegram chat",
        }
    
    def create_plan(self, goal: str, context: Dict[str, Any] = None) -> ExecutionPlan:
        """
        Create an execution plan for a goal.
        
        Args:
            goal: High-level goal description
            context: Additional context (blackboard state, recent messages, etc.)
            
        Returns:
            Execution plan with ordered steps
        """
        plan_id = str(uuid.uuid4())
        
        # Generate plan (LLM if available, else rule-based)
        steps = self._generate_steps(goal, context)
        
        # Create execution plan
        plan = ExecutionPlan(
            plan_id=plan_id,
            goal=goal,
            steps=steps,
            status="pending"
        )
        
        return plan
    
    def _generate_steps(self, goal: str, context: Dict[str, Any] = None) -> List[PlanStep]:
        """
        Generate execution steps using LLM.
        
        Args:
            goal: Task goal
            context: Additional context
            
        Returns:
            List of plan steps with dependencies
        """
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nAvailable context:\n"
            for key, value in context.items():
                context_str += f"  {key}: {value}\n"
        
        # Build tool catalog string
        tools_str = "\n".join([f"  - {name}: {desc}" for name, desc in self.tool_catalog.items()])
        
        prompt = f"""You are a task planning assistant. Given a user goal, break it down into a sequence of concrete execution steps.

Available tools:
{tools_str}

User goal: {goal}{context_str}

Generate a step-by-step execution plan. For each step:
1. Assign a step_id (step1, step2, etc.)
2. Select the appropriate tool
3. Specify tool arguments (use placeholders like {{prev_step_output}} for values from previous steps)
4. List dependencies (step_ids this step depends on)
5. Provide a clear description

Format your response as a JSON array of steps:
[
  {{
    "step_id": "step1",
    "tool": "tool_name",
    "args": {{"arg1": "value1"}},
    "depends_on": [],
    "description": "Human-readable description"
  }},
  ...
]

Important:
- For multi-step tasks, ensure proper dependency ordering
- Use descriptive step_ids
- You MUST only use tools from the Available tools list above
- NEVER use tools like "python", "execute", "run", or any tool not in the Available tools list
- For F1 standings: use extract_webpage with URL https://www.formula1.com/en/results/2025/drivers to scrape the driver standings table
- For Google Sheets: use google_sheets_upsert with spreadsheet_title, sheet_name, rows
- For sharing: use google_drive_share with file_id from previous step
  * For public sharing (anyone with link): {{"type": "anyone", "role": "reader"}}
  * For private sharing with user: {{"type": "user", "role": "reader"}} (email will be auto-populated from SELF_EMAIL)
  * Default to type="anyone" unless explicitly sharing with specific person
- For emails: use gmail_send with to, subject, html, and optional attachments
  * When sending to "myself" or "self", leave "to" field empty or use "myself" - it will be auto-populated from SELF_EMAIL
  * For sending to others, provide explicit email address in "to" field

CRITICAL: Only use tool names exactly as listed in "Available tools" above. Invalid tool names will cause the plan to fail.

Respond with ONLY the JSON array, no additional text."""

        # If LLM client unavailable, use rule-based fallback
        if self.client is None:
            return self._rule_based_plan(goal)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            # Parse response
            import json
            response_text = response.text.strip()
            
            # Extract JSON array from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            steps_data = json.loads(response_text)
            
            # Convert to PlanStep objects with validation
            steps = []
            valid_tools = set(self.tool_catalog.keys())
            
            for step_data in steps_data:
                tool_name = step_data.get("tool", "")
                
                # Validate tool name - skip invalid tools
                if tool_name not in valid_tools:
                    print(f"Warning: Invalid tool '{tool_name}' in plan step '{step_data.get('step_id', 'unknown')}'. Skipping.")
                    continue
                
                step = PlanStep(
                    step_id=step_data.get("step_id", f"step{len(steps)+1}"),
                    tool=tool_name,
                    args=step_data.get("args", {}),
                    depends_on=step_data.get("depends_on", []),
                    description=step_data.get("description", ""),
                    status="pending"
                )
                steps.append(step)
            
            # If no valid steps generated, fall back to rule-based plan
            if not steps:
                print("Warning: LLM generated no valid steps. Falling back to rule-based plan.")
                return self._rule_based_plan(goal)
            
            return steps
        except Exception as e:
            print(f"Error generating plan: {e}")
            return self._rule_based_plan(goal)

    def _rule_based_plan(self, goal: str) -> List[PlanStep]:
        """Heuristic plan for common tasks when LLM is unavailable."""
        steps: List[PlanStep] = []
        lowered = goal.lower()

        if "f1" in lowered and ("standings" in lowered or "driver" in lowered):
            import re
            import os
            email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", goal)
            # Use SELF_EMAIL from environment, or email found in goal, or placeholder
            to_email = email_match.group(0) if email_match else os.environ.get("SELF_EMAIL", "your_email@example.com")
            # Get F1 URL from environment or use 2025 default
            f1_url = os.environ.get("F1_STANDINGS_URL", "https://www.formula1.com/en/results/2025/drivers")
            
            # 1) Extract webpage (F1 driver standings) using Trafilatura
            steps.append(PlanStep(
                step_id="step1",
                tool="extract_webpage",
                args={"url": f1_url},
                depends_on=[],
                description="Extract 2025 F1 driver standings from web using Trafilatura",
                status="pending"
            ))

            # 2) Create Google Sheet with rows from step1
            steps.append(PlanStep(
                step_id="step2",
                tool="google_sheets_upsert",
                args={
                    "spreadsheet_title": "F1_2025_Driver_Standings",
                    "sheet_name": "Drivers_2025",
                    "rows": "{step1.rows}"
                },
                depends_on=["step1"],
                description="Create/update Google Sheet with 2025 F1 driver standings data",
                status="pending"
            ))

            # 3) Share link (optional downstream)
            steps.append(PlanStep(
                step_id="step3",
                tool="google_drive_share",
                args={"file_id": "{step2.spreadsheet_id}", "role": "reader", "type": "anyone"},
                depends_on=["step2"],
                description="Create shareable link for the spreadsheet",
                status="pending"
            ))

            # 4) Gmail send (optional; address cannot be reliably parsed here)
            steps.append(PlanStep(
                step_id="step4",
                tool="gmail_send",
                args={
                    "to": to_email,
                    "subject": "F1 Standings Sheet",
                    "html": "F1 standings sheet: {step3.link}",
                },
                depends_on=["step3"],
                description="Email sheet link",
                status="pending"
            ))
            return steps

        # Default minimal single-step when no heuristic matches
        return [PlanStep(
            step_id="step1",
            tool="extract_webpage",
            args={"url": "https://example.com"},
            depends_on=[],
            description=f"Execute goal: {goal}",
            status="pending"
        )]
    
    def refine_plan(self, plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """
        Refine an existing plan based on feedback or errors.
        
        Args:
            plan: Current execution plan
            feedback: Feedback or error message
            
        Returns:
            Updated execution plan
        """
        # Generate refined steps
        prompt = f"""The following execution plan encountered an issue:

Goal: {plan.goal}

Current steps:
{self._format_plan_steps(plan.steps)}

Issue/Feedback: {feedback}

Generate a refined plan to address the issue. Respond with a JSON array of steps in the same format as before."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            import json
            response_text = response.text.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            steps_data = json.loads(response_text)
            
            # Update plan with refined steps (with validation)
            new_steps = []
            valid_tools = set(self.tool_catalog.keys())
            
            for step_data in steps_data:
                tool_name = step_data.get("tool", "")
                
                # Validate tool name - skip invalid tools
                if tool_name not in valid_tools:
                    print(f"Warning: Invalid tool '{tool_name}' in refined plan step '{step_data.get('step_id', 'unknown')}'. Skipping.")
                    continue
                
                step = PlanStep(
                    step_id=step_data.get("step_id", f"step{len(new_steps)+1}"),
                    tool=tool_name,
                    args=step_data.get("args", {}),
                    depends_on=step_data.get("depends_on", []),
                    description=step_data.get("description", ""),
                    status="pending"
                )
                new_steps.append(step)
            
            # If no valid steps, keep original plan
            if not new_steps:
                print("Warning: Refined plan has no valid steps. Keeping original plan.")
                return plan
            
            plan.steps = new_steps
            plan.status = "pending"
            
            return plan
        except Exception as e:
            print(f"Error refining plan: {e}")
            return plan
    
    def _format_plan_steps(self, steps: List[PlanStep]) -> str:
        """Format plan steps as human-readable text."""
        lines = []
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. [{step.step_id}] {step.description}")
            lines.append(f"   Tool: {step.tool}")
            lines.append(f"   Status: {step.status}")
            if step.depends_on:
                lines.append(f"   Depends on: {', '.join(step.depends_on)}")
        return "\n".join(lines)

