
import asyncio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("GEMINI_API_KEY")

async def main():
    if not API_KEY:
        print("Error: No API_KEY")
        return

    # 1. 執行戶口普查：列出所有可用模型
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    print(f"[Listing Models] querying {url[:60]}...")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                print(f"\n[OK] Found {len(models)} models:")
                for m in models:
                    name = m.get("name", "unknown")
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        print(f"  - {name} (Supported)")
                
                # 找出一個 Flash 模型
                flash_models = [m["name"] for m in models if "flash" in m["name"].lower()]
                if flash_models:
                    print(f"\n>>> Recommended Flash Model: {flash_models[0]}")
                else:
                    print("\n>>> No Flash model found, using first supported model.")
            else:
                print(f"[Fail] HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
