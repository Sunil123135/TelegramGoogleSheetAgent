"""
Cursor Agent - Main Entry Point

Multi-layer agent with Perception-Memory-Decision-Action architecture.
"""

import asyncio
import os
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

from agent.orchestrator import CursorAgent


async def run_f1_standings_workflow():
    """
    Example: F1 standings workflow.
    
    Workflow:
    1. Extract F1 standings from web page
    2. Create Google Sheet with data
    3. Share the sheet
    4. Send email with link
    5. Send Telegram confirmation
    """
    print("=" * 60)
    print("Cursor Agent - F1 Standings Workflow")
    print("=" * 60)
    
    # Initialize agent
    agent = CursorAgent()
    
    # Define the workflow goal
    goal = """Find the Current Point Standings of F1 Racers, then put that into a 
Google Excel Sheet, and then share the link to this sheet with yourself on Gmail"""
    
    print(f"\n🎯 Goal: {goal}\n")
    
    # Execute workflow
    result = await agent.execute_workflow(goal)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result["success"]:
        print("✅ Workflow completed successfully!\n")
        
        plan = result["plan"]
        blackboard = result["blackboard"]
        
        print(f"📋 Plan: {len(plan.steps)} steps")
        for i, step in enumerate(plan.steps, 1):
            status_icon = "✓" if step.status == "completed" else "✗"
            print(f"  {status_icon} {i}. {step.description}")
        
        print(f"\n📊 Outputs:")
        for key, value in blackboard.items():
            if not key.startswith("step_"):
                print(f"  - {key}: {value}")
    else:
        print("❌ Workflow failed\n")
        plan = result["plan"]
        for step in plan.steps:
            if step.status == "failed":
                print(f"Failed at: {step.description}")
                if step.result:
                    print(f"Error: {step.result.error}")
    
    # Save state
    agent.save_state()
    
    print("\n" + "=" * 60)


async def run_interactive_mode():
    """Run agent in interactive mode."""
    print("=" * 60)
    print("Cursor Agent - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your message to interact with the agent")
    print("  - Type 'ingest <url>' to ingest a document")
    print("  - Type 'memory' to see memory summary")
    print("  - Type 'exit' to quit")
    print("\n" + "=" * 60 + "\n")
    
    agent = CursorAgent()
    conversation_id = "interactive"
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "memory":
                summary = agent.get_memory_summary(conversation_id)
                print(f"\n📚 {summary}")
                continue
            
            if user_input.lower().startswith("ingest "):
                uri = user_input[7:].strip()
                print(f"\n🔄 Ingesting {uri}...")
                doc_id = await agent.ingest_document(uri, conversation_id=conversation_id)
                print(f"✅ Document ingested: {doc_id}")
                continue
            
            # Process message
            print("\n🤖 Agent: Processing...\n")
            response = await agent.process_message(user_input, conversation_id)
            print(f"🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Save state on exit
    agent.save_state()


def setup_environment():
    """Set up environment and directories."""
    # Load environment variables
    load_dotenv()
    
    # Create necessary directories
    directories = [
        "./data",
        "./data/faiss_index",
        "./data/temp",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Check for required environment variables
    required_vars = [
        # Uncomment when using real APIs
        # "GOOGLE_CLIENT_SECRET_PATH",
        # "TELEGRAM_BOT_TOKEN",
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing)}")
        print("   Check env.example for required configuration")


async def main():
    """Main entry point."""
    setup_environment()
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            await run_interactive_mode()
        elif sys.argv[1] == "f1":
            await run_f1_standings_workflow()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("\nUsage:")
            print("  python main.py interactive  - Run in interactive mode")
            print("  python main.py f1          - Run F1 standings workflow")
    else:
        # Default: run F1 workflow
        await run_f1_standings_workflow()


if __name__ == "__main__":
    asyncio.run(main())
