"""
Tool selection and argument resolution.

Resolves placeholder arguments from blackboard and previous step outputs.
"""

import re
from typing import Dict, Any, List, Optional
from ..models import PlanStep, ToolRequest


class ToolSelector:
    """Selects and prepares tools for execution."""
    
    def __init__(self):
        """Initialize tool selector."""
        self.placeholder_pattern = re.compile(r'\{([^}]+)\}')
    
    def prepare_tool_request(
        self,
        step: PlanStep,
        blackboard: Dict[str, Any],
        step_results: Dict[str, Dict[str, Any]] = None
    ) -> ToolRequest:
        """
        Prepare a tool request by resolving arguments.
        
        Args:
            step: Plan step to execute
            blackboard: Shared state
            step_results: Results from completed steps (step_id -> output)
            
        Returns:
            Tool request with resolved arguments
        """
        if step_results is None:
            step_results = {}
        
        # Pre-process args to handle {prev_step_output} placeholder
        # Map {prev_step_output} to the most recent dependency step
        preprocessed_args = self._preprocess_placeholders(step.args, step.depends_on, step_results)
        
        # Resolve arguments
        resolved_args = self._resolve_arguments(
            preprocessed_args,
            blackboard,
            step_results
        )
        
        return ToolRequest(
            name=step.tool,
            args=resolved_args,
            depends_on=step.depends_on,
            request_id=step.step_id
        )
    
    def _preprocess_placeholders(
        self,
        args: Dict[str, Any],
        depends_on: List[str],
        step_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Pre-process placeholders to handle generic ones like {prev_step_output}.
        
        Args:
            args: Raw arguments
            depends_on: List of dependency step IDs
            step_results: Results from previous steps
            
        Returns:
            Preprocessed arguments with generic placeholders resolved
        """
        preprocessed = {}
        
        for key, value in args.items():
            if isinstance(value, str):
                # Find all placeholders in the string
                matches = self.placeholder_pattern.findall(value)
                for ph in matches:
                    # Handle {prev_step_output} and {step_output}
                    if ph in ("prev_step_output", "step_output", "previous_output"):
                        # Most recent dependency step
                        prev_step_id = None
                        for dep_id in reversed(depends_on):
                            if dep_id in step_results:
                                prev_step_id = dep_id
                                break
                        if prev_step_id:
                            prev_output = step_results[prev_step_id]
                            if "rows" in prev_output:
                                value = value.replace(f"{{{ph}}}", f"{{{prev_step_id}.rows}}")
                            elif "data_rows" in prev_output:
                                value = value.replace(f"{{{ph}}}", f"{{{prev_step_id}.data_rows}}")
                            elif "output" in prev_output:
                                value = value.replace(f"{{{ph}}}", f"{{{prev_step_id}.output}}")
                            else:
                                keys = list(prev_output.keys())
                                if keys:
                                    value = value.replace(f"{{{ph}}}", f"{{{prev_step_id}.{keys[0]}}}")
                    # Handle {stepN_output} → {stepN.rows} or similar
                    elif re.match(r"^step\d+_output$", ph):
                        step_id = ph.split("_")[0]  # e.g., step1_output -> step1
                        if step_id in step_results:
                            out = step_results[step_id]
                            if "rows" in out:
                                value = value.replace(f"{{{ph}}}", f"{{{step_id}.rows}}")
                            elif "data_rows" in out:
                                value = value.replace(f"{{{ph}}}", f"{{{step_id}.data_rows}}")
                            elif "output" in out:
                                value = value.replace(f"{{{ph}}}", f"{{{step_id}.output}}")
                            else:
                                keys = list(out.keys())
                                if keys:
                                    value = value.replace(f"{{{ph}}}", f"{{{step_id}.{keys[0]}}}")
                
                preprocessed[key] = value
            elif isinstance(value, list):
                preprocessed_list = []
                for v in value:
                    if isinstance(v, str):
                        # Recursively preprocess strings in lists
                        preprocessed_item = self._preprocess_placeholders({"temp": v}, depends_on, step_results)["temp"]
                        preprocessed_list.append(preprocessed_item)
                    elif isinstance(v, dict):
                        preprocessed_list.append(self._preprocess_placeholders(v, depends_on, step_results))
                    else:
                        preprocessed_list.append(v)
                preprocessed[key] = preprocessed_list
            elif isinstance(value, dict):
                preprocessed[key] = self._preprocess_placeholders(value, depends_on, step_results)
            else:
                preprocessed[key] = value
        
        return preprocessed
    
    def _resolve_arguments(
        self,
        args: Dict[str, Any],
        blackboard: Dict[str, Any],
        step_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve placeholder arguments.
        
        Placeholders can reference:
        - Blackboard values: {blackboard.key}
        - Previous step outputs: {step1.output_key}
        - Environment variables: {env.VAR_NAME}
        
        Args:
            args: Raw arguments with placeholders
            blackboard: Shared state
            step_results: Results from previous steps
            
        Returns:
            Arguments with placeholders resolved
        """
        resolved = {}
        
        for key, value in args.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_string(value, blackboard, step_results)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_string(v, blackboard, step_results) if isinstance(v, str) else v
                    for v in value
                ]
            elif isinstance(value, dict):
                resolved[key] = self._resolve_arguments(value, blackboard, step_results)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_string(
        self,
        value: str,
        blackboard: Dict[str, Any],
        step_results: Dict[str, Dict[str, Any]]
    ) -> Any:
        """Resolve a single string value with placeholders."""
        # Find all placeholders
        matches = self.placeholder_pattern.findall(value)
        
        if not matches:
            return value
        
        # If entire value is a single placeholder, return the actual value (not string)
        if len(matches) == 1 and value == f"{{{matches[0]}}}":
            return self._resolve_placeholder(matches[0], blackboard, step_results)
        
        # Multiple placeholders or mixed - do string substitution
        result = value
        for match in matches:
            placeholder = f"{{{match}}}"
            resolved = self._resolve_placeholder(match, blackboard, step_results)
            result = result.replace(placeholder, str(resolved))
        
        return result
    
    def _resolve_placeholder(
        self,
        placeholder: str,
        blackboard: Dict[str, Any],
        step_results: Dict[str, Dict[str, Any]]
    ) -> Any:
        """Resolve a single placeholder reference."""
        parts = placeholder.split(".")
        
        if len(parts) < 2:
            # Simple blackboard lookup
            return blackboard.get(placeholder, f"{{{placeholder}}}")
        
        source = parts[0]
        path = parts[1:]
        
        if source == "blackboard":
            # Blackboard reference
            value = blackboard
            for part in path:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return f"{{{placeholder}}}"
            return value
        
        elif source in step_results:
            # Step result reference
            value = step_results[source]
            for part in path:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return f"{{{placeholder}}}"
            return value
        
        elif source == "env":
            # Environment variable
            import os
            return os.environ.get(path[0], f"{{{placeholder}}}")
        
        else:
            # Unknown source, return as-is
            return f"{{{placeholder}}}"
    
    def validate_tool_request(self, request: ToolRequest) -> tuple[bool, Optional[str]]:
        """
        Validate that a tool request has all required arguments.
        
        Args:
            request: Tool request to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Define required arguments for each tool
        required_args = {
            "extract_webpage": ["url"],
            "extract_pdf": ["path"],
            "caption_image": ["image_url_or_path"],
            "google_sheets_upsert": ["spreadsheet_title", "sheet_name", "rows"],
            "google_drive_share": ["file_id"],
            "gmail_send": ["to", "subject"],
            "telegram_send": ["chat_id", "text"],
        }
        
        tool_name = request.name
        if tool_name not in required_args:
            return True, None  # Unknown tool, assume valid
        
        # Check required arguments
        for arg in required_args[tool_name]:
            if arg not in request.args or request.args[arg] is None:
                return False, f"Missing required argument: {arg}"
            
            # Check for unresolved placeholders
            value = request.args[arg]
            if isinstance(value, str) and "{" in value and "}" in value:
                return False, f"Unresolved placeholder in argument: {arg} = {value}"
        
        return True, None
    
    def can_execute_step(
        self,
        step: PlanStep,
        completed_steps: List[str]
    ) -> bool:
        """
        Check if a step's dependencies are satisfied.
        
        Args:
            step: Step to check
            completed_steps: List of completed step IDs
            
        Returns:
            True if all dependencies are met
        """
        for dep in step.depends_on:
            if dep not in completed_steps:
                return False
        return True

