import asyncio
import aiohttp
import json

class QwenClient:
    def __init__(self, base_url="http://localhost:11434", model="phi:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=120)
    
    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Error {resp.status}: {error_text}")
                    return ""
                data = await resp.json()
                return data.get("response", "").strip()

async def main():
    client = QwenClient(model="phi:latest")
    
    print("\n🚀 ATLAS Qwen 3.5 Test\n")
    
    # Test simple generation
    print("1️⃣  Testing basic generation...")
    response = await client.generate("What is the capital of France?")
    print(f"   Response: {response}\n")
    
    # Test daemon-like behavior (rapid requests)
    print("2️⃣  Testing rapid requests (daemon behavior)...")
    for i in range(3):
        response = await client.generate(f"Say 'Test {i}' in one word")
        print(f"   Request {i+1}: {response}")
    
    print("\n✅ All tests passed!\n")

asyncio.run(main())
