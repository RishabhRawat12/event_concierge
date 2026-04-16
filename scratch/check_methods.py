import asyncio
from google import genai
import os

async def check():
    client = genai.Client(api_key="TEST")
    print("Sync Client methods:", dir(client.chats))
    print("Async Client methods:", dir(client.aio.chats))
    
    # Mocking a chat to see its methods
    # chat = client.chats.create(model='gemini-2.0-flash')
    # print("Chat methods:", dir(chat))
    
    # async_chat = client.aio.chats.create(model='gemini-2.0-flash')
    # print("AsyncChat methods:", dir(async_chat))

if __name__ == "__main__":
    asyncio.run(check())
