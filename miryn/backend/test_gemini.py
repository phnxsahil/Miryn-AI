import asyncio
import os
import pytest
from google import genai
from google.genai import types

@pytest.mark.anyio
async def test_stream():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)
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
