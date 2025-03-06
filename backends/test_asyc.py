import aiohttp
import asyncio
import json

async def fetch(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def main():
    url = "http://127.0.0.1:5000/async_chat"

    input_text = """
    Say only test
    
    """
    input_text = input_text.strip()

    data = {
        "input_text": input_text,
        "chatbot_name": "Summarizers",
        "interaction_id": "1234567890",
        "system_prompt": "You are a helpful assistant that summarizes text."
    }

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url, data) for _ in range(1000)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            print(response)

if __name__ == "__main__":
    asyncio.run(main())  