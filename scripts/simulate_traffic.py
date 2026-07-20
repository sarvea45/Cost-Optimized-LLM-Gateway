import os
import asyncio
import httpx
import time

API_URL = "http://localhost:8000/v1/completions"

# 50 diverse prompts
prompts = [
    "What is the capital of France?",
    "Write a python function to reverse a string.",
    "Analyze the architectural differences between microservices and monolithic applications.", # complex
    "Who won the world cup in 2022?",
    "What is the capital of France?", # Repeat
    "Explain quantum computing in simple terms.",
    "Can you architect a cloud solution for a retail company?", # complex
    "Tell me a joke.",
    "Write a short poem about the sea.",
    "Analyze the financial markets.",
] * 5  # Just repeating to get 50

async def main():
    print(f"Sending {len(prompts)} requests...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, prompt in enumerate(prompts):
            print(f"[{i+1}/{len(prompts)}] Sending prompt: {prompt[:30]}...")
            
            try:
                start = time.time()
                response = await client.post(API_URL, json={
                    "prompt": prompt,
                    "user_id": f"user_{i%5}"
                })
                latency = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  -> Model: {data.get('model_used')}, Cache Hit: {data.get('cache_hit')}, Cost: ${data.get('cost_usd', 0):.6f}, Latency: {latency:.2f}s")
                else:
                    print(f"  -> Error: {response.status_code}")
            except Exception as e:
                print(f"  -> Exception: {e}")
                
            await asyncio.sleep(0.5)
            
    print("Done. Check the analytics endpoint to see the summary.")

if __name__ == "__main__":
    asyncio.run(main())
