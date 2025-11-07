"""
Tool execution engine.

Orchestrates tool calls via MCP servers and manages execution state.
"""

import asyncio
import os
from typing import Dict, Any, List
from datetime import datetime
from ..models import ToolRequest, ToolResult, ExecutionPlan, PlanStep


class ToolExecutor:
    """Executes tool requests via MCP servers."""
    
    def __init__(self, use_sse: bool = None):
        """
        Initialize tool executor.
        
        Args:
            use_sse: Whether to use SSE MCP servers instead of direct calls.
                     If None, reads from environment variable USE_SSE_MCP (default: True)
        """
        if use_sse is None:
            use_sse = os.environ.get('USE_SSE_MCP', 'true').lower() == 'true'
        
        self.use_sse = use_sse
        self.client_pool = None
        
        if self.use_sse:
            from mcp_servers.sse_client import get_client_pool
            self.client_pool = get_client_pool()
        
        self.tool_handlers = {
            "extract_webpage": self._extract_webpage,
            "extract_pdf": self._extract_pdf,
            "caption_image": self._caption_image,
            "google_sheets_upsert": self._google_sheets_upsert,
            "google_drive_share": self._google_drive_share,
            "gmail_send": self._gmail_send,
            "telegram_send": self._telegram_send,
        }
    
    async def execute_tool(self, request: ToolRequest) -> ToolResult:
        """
        Execute a single tool request.
        
        Args:
            request: Tool request to execute
            
        Returns:
            Tool execution result
        """
        handler = self.tool_handlers.get(request.name)
        
        if handler is None:
            return ToolResult(
                request_id=request.request_id,
                name=request.name,
                success=False,
                error=f"Unknown tool: {request.name}"
            )
        
        try:
            output = await handler(request.args)
            return ToolResult(
                request_id=request.request_id,
                name=request.name,
                success=True,
                output=output
            )
        except Exception as e:
            return ToolResult(
                request_id=request.request_id,
                name=request.name,
                success=False,
                error=str(e)
            )
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        blackboard: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Execute an entire plan with dependency management.
        
        Args:
            plan: Execution plan
            blackboard: Shared state (updated with results)
            
        Returns:
            Tuple of (success, final_blackboard)
        """
        completed_steps = []
        step_results = {}
        
        plan.status = "in_progress"
        
        # Execute steps in dependency order
        pending_steps = list(plan.steps)
        
        while pending_steps:
            # Find steps that can execute now
            executable = [
                step for step in pending_steps
                if all(dep in completed_steps for dep in step.depends_on)
            ]
            
            if not executable:
                # Circular dependency or missing dependency
                plan.status = "failed"
                return False, blackboard
            
            # Execute all independent steps in parallel
            tasks = []
            for step in executable:
                step.status = "in_progress"
                
                # Resolve arguments
                from ..decision.tool_selector import ToolSelector
                selector = ToolSelector()
                tool_request = selector.prepare_tool_request(step, blackboard, step_results)
                
                # Validate
                valid, error = selector.validate_tool_request(tool_request)
                if not valid:
                    step.status = "failed"
                    step.result = ToolResult(
                        request_id=step.step_id,
                        name=step.tool,
                        success=False,
                        error=error
                    )
                    plan.status = "failed"
                    return False, blackboard
                
                # Execute
                tasks.append((step, self.execute_tool(tool_request)))
            
            # Wait for all parallel tasks
            for step, task in tasks:
                result = await task
                step.result = result
                
                if result.success:
                    step.status = "completed"
                    completed_steps.append(step.step_id)
                    step_results[step.step_id] = result.output
                    
                    # Update blackboard with key outputs
                    self._update_blackboard(blackboard, step, result.output)
                else:
                    step.status = "failed"
                    plan.status = "failed"
                    return False, blackboard
            
            # Remove completed steps from pending
            pending_steps = [s for s in pending_steps if s not in executable]
        
        plan.status = "completed"
        plan.completed_at = datetime.now()
        
        return True, blackboard
    
    def _update_blackboard(
        self,
        blackboard: Dict[str, Any],
        step: PlanStep,
        output: Dict[str, Any]
    ):
        """Update blackboard with step outputs using semantic keys."""
        # Map tool outputs to canonical blackboard keys
        key_mappings = {
            "google_sheets_upsert": {
                "spreadsheet_id": "spreadsheet_id",
                "sheet_url": "sheet_url",
            },
            "google_drive_share": {
                "link": "share_link",
            },
            "gmail_send": {
                "message_id": "email_message_id",
            },
            "extract_webpage": {
                "markdown": "extracted_content",
                "rows": "data_rows",
            },
        }
        
        mappings = key_mappings.get(step.tool, {})
        for output_key, blackboard_key in mappings.items():
            if output_key in output:
                blackboard[blackboard_key] = output[output_key]
        
        # Also store under step ID for explicit reference
        blackboard[f"step_{step.step_id}"] = output
    
    # Tool handler implementations (call MCP servers)
    
    async def _extract_webpage(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract webpage to markdown via Trafilatura MCP server."""
        
        # Use SSE client if enabled
        if self.use_sse and self.client_pool:
            result = await self.client_pool.call_tool(
                server_name="trafilatura",
                tool_name="fetch_markdown",
                arguments={"url": args["url"]}
            )
            
            if "error" in result:
                raise RuntimeError(f"SSE server error: {result['error']}")
            
            markdown = result.get("markdown", "")
            rows = self._parse_markdown_table(markdown)
            
            # Fallback for F1 standings
            if not rows or len(rows) < 2:
                try:
                    html_rows = self._extract_f1_standings_from_html(args["url"])
                    if html_rows and len(html_rows) >= 2:
                        rows = html_rows
                except Exception as e:
                    print(f"Warning: HTML extraction failed: {str(e)[:100]}")
            
            return {
                "markdown": markdown,
                "rows": rows,
                "url": args["url"]
            }
        
        # Fallback to direct call
        from ..perception.ingestion import DocumentIngestion
        from ..models import SourceKind
        
        ingestion = DocumentIngestion()
        doc, markdown = ingestion.ingest_document(args["url"], SourceKind.HTML)
        
        # Parse markdown table if it exists (for F1 standings, etc.)
        rows = self._parse_markdown_table(markdown)

        # Fallback: if no rows parsed from markdown, try HTML parsing for F1 standings
        if not rows or len(rows) < 2:
            try:
                html_rows = self._extract_f1_standings_from_html(args["url"])
                if html_rows and len(html_rows) >= 2:
                    rows = html_rows
            except Exception as e:
                # Log error but keep rows as-is if fallback fails
                print(f"Warning: HTML extraction failed: {str(e)[:100]}")
        
        return {
            "markdown": markdown,
            "doc_id": doc.doc_id,
            "rows": rows
        }
    
    async def _extract_pdf(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PDF to markdown via MuPDF4LLM MCP server."""
        from ..perception.ingestion import DocumentIngestion
        from ..models import SourceKind
        
        ingestion = DocumentIngestion()
        doc, markdown = ingestion.ingest_document(args["path"], SourceKind.PDF)
        
        return {
            "markdown": markdown,
            "doc_id": doc.doc_id
        }
    
    async def _caption_image(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image caption via Gemma MCP server."""
        # Placeholder - in production, call Gemma MCP server
        image_ref = args["image_url_or_path"]
        alt_text = f"Image: {image_ref}"
        
        return {
            "alt_text": alt_text,
            "image_ref": image_ref
        }
    
    async def _google_sheets_upsert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create/update Google Sheet via MCP server."""
        
        # Use SSE client if enabled
        if self.use_sse and self.client_pool:
            result = await self.client_pool.call_tool(
                server_name="google_sheets",
                tool_name="upsert_table",
                arguments=args
            )
            
            if "error" in result:
                raise RuntimeError(f"SSE server error: {result['error']}")
            
            return result
        
        # Fallback to direct call
        title = args["spreadsheet_title"]
        sheet_name = args["sheet_name"]
        rows = args["rows"]

        from mcp_servers.google_sheets_stdio import GoogleSheetsServer

        server = GoogleSheetsServer()
        result = await server.upsert_table(
            spreadsheet_title=title,
            sheet_name=sheet_name,
            rows=rows
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result
    
    async def _google_drive_share(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Share Google Drive file via MCP server."""
        import os
        
        file_id = args["file_id"]
        role = args.get("role", "reader")
        share_type = args.get("type", "anyone")
        email = args.get("email")
        
        # If sharing with 'user' or 'group' type but no email provided, use SELF_EMAIL
        if share_type in ["user", "group"] and not email:
            self_email = os.environ.get("SELF_EMAIL", "").strip()
            if self_email:
                email = self_email
                print(f"[INFO] Using SELF_EMAIL for {share_type} share: {email}")
            else:
                raise RuntimeError(
                    f"Cannot share with type '{share_type}': email is required but not provided. "
                    f"Either provide 'email' argument or set SELF_EMAIL environment variable."
                )
        
        # Use SSE client if enabled
        if self.use_sse and self.client_pool:
            result = await self.client_pool.call_tool(
                server_name="google_drive",
                tool_name="share",
                arguments={
                    "file_id": file_id,
                    "role": role,
                    "type": share_type,
                    "email": email
                }
            )
            
            if "error" in result:
                raise RuntimeError(f"SSE server error: {result['error']}")
            
            return result

        # Fallback to direct call
        from mcp_servers.google_drive_stdio import GoogleDriveServer

        server = GoogleDriveServer()
        result = await server.share(
            file_id=file_id,
            role=role,
            type=share_type,
            email=email
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result
    
    async def _gmail_send(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via MCP server."""
        import os
        import re
        
        to = args.get("to", "")
        
        # If "to" is empty, refers to "myself", or has unresolved placeholder, use SELF_EMAIL
        if not to or to.strip() in ["", "myself", "me"] or "{" in to:
            self_email = os.environ.get("SELF_EMAIL", "").strip()
            if self_email:
                to = self_email
                print(f"[INFO] Using SELF_EMAIL as recipient: {to}")
            else:
                raise RuntimeError(
                    "Cannot send email: recipient ('to') is required but not provided. "
                    "Either provide 'to' argument or set SELF_EMAIL environment variable."
                )
        
        # Validate email format
        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        if not re.search(email_pattern, to):
            raise RuntimeError(
                f"Invalid email address format: '{to}'. "
                f"Please provide a valid email address or set SELF_EMAIL environment variable."
            )
        
        subject = args.get("subject", "")
        html = args.get("html", "")
        attachments = args.get("attachments", [])
        
        # Use SSE client if enabled
        if self.use_sse and self.client_pool:
            result = await self.client_pool.call_tool(
                server_name="gmail",
                tool_name="send",
                arguments={
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "attachments": attachments
                }
            )
            
            if "error" in result:
                raise RuntimeError(f"SSE server error: {result['error']}")
            
            return result

        # Fallback to direct call
        from mcp_servers.gmail_stdio import GmailServer

        server = GmailServer()
        result = await server.send(
            to=to,
            subject=subject,
            html=html,
            attachments=attachments
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result
    
    async def _telegram_send(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send Telegram message via MCP server."""
        chat_id = args["chat_id"]
        text = args["text"]
        
        # Mock response
        print(f"[MOCK] Sent Telegram message to {chat_id}")
        print(f"[MOCK] Text: {text[:100]}...")
        
        return {
            "ok": True,
            "chat_id": chat_id,
            "message_id": int(datetime.now().timestamp())
        }
    
    
    def _parse_markdown_table(self, markdown: str) -> List[List[str]]:
        """Parse a markdown table into rows."""
        import re
        
        lines = markdown.split('\n')
        rows = []
        
        for line in lines:
            # Check if line looks like a table row
            if '|' in line and not line.strip().startswith('|-'):
                # Parse cells
                cells = [cell.strip() for cell in line.split('|')]
                # Remove empty first/last cells from leading/trailing pipes
                cells = [c for c in cells if c]
                if cells:
                    rows.append(cells)
        
        return rows

    def _extract_f1_standings_from_html(self, url: str) -> List[List[str]]:
        """Attempt to extract F1 driver standings table directly from HTML.
        Uses Selenium for JavaScript-rendered pages like formula1.com.
        Returns rows including header if found; otherwise empty list.
        """
        import re
        
        # Try Selenium first for JavaScript-rendered pages
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Setup Chrome options for headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            
            # Initialize driver with webdriver-manager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                # Load page
                driver.get(url)
                
                # Wait for table to load (up to 10 seconds)
                wait = WebDriverWait(driver, 10)
                # Common selectors for F1 results tables
                table_selectors = [
                    "table.resultsarchive-table",
                    "table[class*='standings']",
                    "table[class*='results']",
                    ".resultsarchive-table",
                    "table"
                ]
                
                table_element = None
                for selector in table_selectors:
                    try:
                        table_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except Exception:
                        continue
                
                if not table_element:
                    driver.quit()
                    return []
                
                # Get rendered HTML
                html = driver.page_source
                driver.quit()
            except Exception as e:
                driver.quit()
                raise e
                
        except Exception as selenium_error:
            # Fallback to requests if Selenium fails
            print(f"Selenium extraction failed: {str(selenium_error)[:100]}, trying requests fallback...")
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            }
            try:
                import requests
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200 or not resp.text:
                    return []
                html = resp.text
            except Exception:
                return []

        # Prefer BeautifulSoup if available
        try:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(html, "html.parser")

            # Try to find table with specific class, then any table
            table = soup.find("table", class_=re.compile(r"resultsarchive-table|standings"))
            if not table:
                # Fallback to first table element
                table = soup.find("table")
            if not table:
                return []

            # Extract all rows directly
            all_rows: List[List[str]] = []
            for tr in table.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
                if cells:
                    all_rows.append(cells)

            if not all_rows or len(all_rows) < 2:
                return []

            # Return rows as-is (first row is header, rest are data)
            return all_rows
        except Exception:
            # As a very last resort, attempt a regex-based extraction
            # Look for simple table-like lines with driver and points
            lines = html.splitlines()
            data: List[List[str]] = []
            for line in lines:
                line = re.sub(r"<[^>]+>", " ", line)
                line = re.sub(r"\s+", " ", line).strip()
                m = re.search(r"^(\d+)\s+([A-Za-z .'-]+)\s+([A-Za-z .'-]+)\s+(\d+)$", line)
                if m:
                    data.append([m.group(1), m.group(2), m.group(3), m.group(4)])
            if data:
                return [["Position", "Driver", "Team", "Points"]] + data
            return []

