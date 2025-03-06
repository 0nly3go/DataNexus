import os
import asyncio
from aiohttp import ClientSession
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def asy_chat_in(input_text, system_prompt="You are a helpful assistant", model="gpt-4o-mini"):
    try:
        # Add chat messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_text})

        # call api
        async with ClientSession() as session:
            response = await client.chat.completions.create(
                model=model,
                messages=messages
            )

        # get response text
        response_text = response.choices[0].message.content

        return response_text

    except Exception as e:
        error_msg = f"Error in asy_chat_in: {str(e)}"
        print(error_msg)
