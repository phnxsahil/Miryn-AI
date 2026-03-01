import asyncio
import os
from google import genai
from google.genai import types

async def test_stream():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        # Test if it needs await
        print("Testing with await...")
        stream = await client.aio.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents="Say hello",
        )
        async for chunk in stream:
            print(f"Chunk: {chunk.text}")
    except TypeError as e:
        print(f"Await failed: {e}")
        print("Testing without await...")
        async for chunk in client.aio.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents="Say hello",
        ):
            print(f"Chunk: {chunk.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We need a key to even test the call structure usually, 
    # but we can just check if it's a coroutine without a key if we're careful.
    asyncio.run(test_stream())
