from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_in(input_text, system_prompt="You are a helpful assistant", model="gpt-4o-mini"):
    try:
        
        # Add chat messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_text})
        
        # call api
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        # get response text
        response_text = response.choices[0].message.content
        
        return response_text
        
    except Exception as e:
        error_msg = f"Error in chat_in: {str(e)}"
        print(error_msg)
    