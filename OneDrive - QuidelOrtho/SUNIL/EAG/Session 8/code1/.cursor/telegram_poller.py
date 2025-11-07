import os, time, requests, traceback, asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding for Unicode (emojis, etc.)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to Python path to import agent module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv()

from agent.orchestrator import CursorAgent  # your class

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")  # optional filter
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Reuse one agent instance
agent = CursorAgent()

async def handle(text: str) -> str:
    # Simple intent gate: if message contains "standing" & "sheet", run your workflow
    print(f"[DEBUG] Received message: {text}")
    t = text.lower()
    
    if "standing" in t and "sheet" in t:
        print("[DEBUG] Detected F1 workflow trigger!")
        
        # Check if SELF_EMAIL is configured
        self_email = os.environ.get('SELF_EMAIL', '').strip()
        if not self_email:
            error_msg = ("❌ Cannot run F1 workflow: SELF_EMAIL is not configured!\n\n"
                        "Please add your email to the .env file:\n"
                        "SELF_EMAIL=your_email@example.com\n\n"
                        "Then restart the bot.")
            print(f"[ERROR] {error_msg}")
            return error_msg
        
        print("[DEBUG] Starting workflow execution...")
        
        try:
            res = await agent.execute_workflow(
                "Find the Current Point Standings of F1 Racers, then put that into a Google Excel Sheet, and then share the link to this sheet with yourself on Gmail, and share the screenshot"
            )
            
            print(f"[DEBUG] Workflow result: success={res.get('success')}")
            
            if res.get("success"):
                bb = res.get("blackboard", {})
                print(f"[DEBUG] Blackboard keys: {list(bb.keys())}")
                link = bb.get("sheet_url") or bb.get("public_link", "(no link)")
                return f"✅ Done. Sheet: {link}"
            else:
                # include the failing step's error if present
                try:
                    plan = res["plan"]
                    failed = [s for s in plan.steps if s.status == "failed"][0]
                    error_msg = f"❌ Failed at: {failed.description}\nError: {failed.result.error if failed.result else 'No error details'}"
                    print(f"[DEBUG] {error_msg}")
                    return error_msg
                except Exception as e:
                    error_msg = f"❌ Workflow failed: {str(e)}"
                    print(f"[DEBUG] {error_msg}")
                    return error_msg
        except Exception as e:
            error_msg = f"❌ Exception during workflow: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            traceback.print_exc()
            return error_msg
    
    # Fallback: route generic messages to your chat handler
    print("[DEBUG] Using fallback chat handler")
    reply = await agent.process_message(text, conversation_id="telegram")
    return reply[:4000]

def send(chat_id: int, text: str, max_retries: int = 3):
    """Send a message to Telegram with error handling and retries."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API}/sendMessage", 
                json={"chat_id": chat_id, "text": text},
                timeout=10
            )
            response.raise_for_status()  # Raise exception for bad status codes
            
            result = response.json()
            if result.get("ok"):
                print(f"[INFO] Message sent successfully to chat_id={chat_id}")
                return True
            else:
                error_desc = result.get("description", "Unknown error")
                print(f"[ERROR] Telegram API returned ok=false: {error_desc}")
                if "retry after" in error_desc.lower():
                    # Rate limit - wait and retry
                    time.sleep(2 ** attempt)
                    continue
                return False
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout sending message (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"[ERROR] Unexpected error sending message: {e}")
            traceback.print_exc()
            return False
    
    print(f"[ERROR] Failed to send message after {max_retries} attempts")
    return False

def main():
    offset = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("=" * 60)
    print("🤖 Telegram Bot Poller Started")
    print("=" * 60)
    print(f"Bot Token: {BOT_TOKEN[:20]}..." if BOT_TOKEN else "Bot Token: NOT SET")
    print(f"Chat ID Filter: {CHAT_ID if CHAT_ID else 'None (accepting all chats)'}")
    
    self_email = os.environ.get('SELF_EMAIL', '').strip()
    if self_email:
        print(f"Self Email: {self_email}")
    else:
        print("Self Email: ⚠️  NOT SET - F1 workflow will fail!")
        print("             Add SELF_EMAIL=your_email@example.com to .env file")
    
    # Show SSE configuration
    use_sse = os.environ.get('USE_SSE_MCP', 'true').lower() == 'true'
    if use_sse:
        print("MCP Mode: 🌐 SSE Servers (HTTP)")
        print("          Make sure SSE servers are running: python start_sse_servers.py")
    else:
        print("MCP Mode: 📁 Direct stdio calls")
    
    print("=" * 60)
    print("✅ Polling Telegram for messages...")
    print("   Send a message containing 'standing' and 'sheet' to trigger F1 workflow\n")
    
    while True:
        try:
            r = requests.get(
                f"{API}/getUpdates", 
                params={"timeout": 25, "offset": offset},
                timeout=30  # Add timeout slightly longer than Telegram's timeout
            )
            r.raise_for_status()  # Raise exception for HTTP errors
            data = r.json()
            
            if not data.get("ok"):
                error_code = data.get("error_code")
                error_desc = data.get("description", "Unknown error")
                print(f"[ERROR] Telegram API error (code {error_code}): {error_desc}")
                
                # Handle specific error codes
                if error_code == 401:
                    print("[FATAL] Invalid bot token. Please check TELEGRAM_BOT_TOKEN in .env file")
                    break
                elif error_code == 409:
                    print("[FATAL] Conflict: Another instance is running. Stop other instances.")
                    break
                
                time.sleep(5)
                continue
            
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if not msg: 
                    continue
                
                chat_id = msg["chat"]["id"]
                username = msg.get("from", {}).get("username", "unknown")
                
                print(f"\n[INFO] Received message from chat_id={chat_id}, username=@{username}")
                
                if CHAT_ID and str(chat_id) != str(CHAT_ID):
                    print(f"[WARN] Ignoring message from unauthorized chat_id: {chat_id}")
                    print(f"       Expected chat_id: {CHAT_ID}")
                    print(f"       To accept messages from this chat, update TELEGRAM_CHAT_ID={chat_id} in your .env file")
                    print(f"       Or remove TELEGRAM_CHAT_ID from .env to accept all chats")
                    continue
                
                text = msg.get("text") or ""
                if not text: 
                    print("[INFO] Message has no text, skipping")
                    continue
                
                try:
                    print(f"[INFO] Processing message...")
                    out = loop.run_until_complete(handle(text))
                    print(f"[INFO] Sending response to chat_id={chat_id}")
                    send(chat_id, out)
                    print("[INFO] Response sent successfully")
                except Exception as e:
                    error_msg = "⚠️ Agent error. Check server logs."
                    print(f"[ERROR] Exception in message handler: {e}")
                    send(chat_id, error_msg)
                    traceback.print_exc()
        except KeyboardInterrupt:
            print("\n\n[INFO] Bot stopped by user")
            break
        except requests.exceptions.Timeout:
            print("[WARN] Request timed out. Retrying...")
            time.sleep(2)
        except requests.exceptions.ConnectionError as e:
            print(f"[WARN] Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request error: {e}")
            traceback.print_exc()
            time.sleep(3)
        except Exception as e:
            print(f"[ERROR] Unexpected polling error: {e}")
            traceback.print_exc()
            time.sleep(3)

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!\n"
                        "Please create a .env file with your bot token:\n"
                        "TELEGRAM_BOT_TOKEN=your_token_here")
    
    # Validate bot token format
    if not BOT_TOKEN.strip():
        raise SystemExit("❌ ERROR: TELEGRAM_BOT_TOKEN is empty")
    
    # Test API connection before starting the main loop
    print("🔍 Testing Telegram API connection...")
    try:
        test_response = requests.get(f"{API}/getMe", timeout=10)
        test_response.raise_for_status()
        test_data = test_response.json()
        
        if test_data.get("ok"):
            bot_info = test_data.get("result", {})
            print(f"✅ Successfully connected to Telegram API")
            print(f"   Bot username: @{bot_info.get('username', 'unknown')}")
            print(f"   Bot name: {bot_info.get('first_name', 'unknown')}")
        else:
            error_desc = test_data.get("description", "Unknown error")
            raise SystemExit(f"❌ ERROR: Telegram API test failed: {error_desc}\n"
                           "Please check your TELEGRAM_BOT_TOKEN")
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"❌ ERROR: Cannot connect to Telegram API: {e}\n"
                        "Please check your internet connection and bot token")
    except Exception as e:
        raise SystemExit(f"❌ ERROR: Unexpected error during API test: {e}")
    
    main()
