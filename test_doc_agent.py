import asyncio
import logging
from src.core.dependencies import get_assistant_service

logging.basicConfig(level=logging.INFO)

async def main():
    assistant = get_assistant_service()
    
    session_id = "test_user_123"
    
    print("Sending message 1 (setting preference)...")
    await assistant.answer_question("Hi, I prefer python code and my API key is xyz123", conversation_id=session_id)
    
    # Wait briefly for background task to finish saving memory
    await asyncio.sleep(2)
    
    print("\nSending message 2 (asking question)...")
    response = await assistant.answer_question("how do i search for the job data? i need a code in java", conversation_id=session_id)
    
    print("\n\n--- FINAL ANSWER ---")
    print(response.answer)
    print("\n--- ENDPOINTS ---")
    for ep in response.endpoints:
        print(f"{ep.method} {ep.url}")

if __name__ == "__main__":
    asyncio.run(main())
