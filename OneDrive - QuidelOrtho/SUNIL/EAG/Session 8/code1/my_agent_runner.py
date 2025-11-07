import sys
import asyncio


async def main() -> None:
    from agent.orchestrator import CursorAgent

    # Read full stdin as the user message
    user_message = sys.stdin.read().strip()
    if not user_message:
        print("No input provided.")
        return

    agent = CursorAgent()
    # Use a stable conversation id for Telegram session context
    conversation_id = "telegram"

    try:
        response = await agent.process_message(user_message, conversation_id=conversation_id)
        # Print a single-line response for the poller to relay
        print(response.replace("\n", " "))
    except Exception as e:
        print(f"Agent error: {e}")


if __name__ == "__main__":
    asyncio.run(main())



