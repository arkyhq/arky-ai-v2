import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PEXELS_API_KEY")

headers = {
    "Authorization": API_KEY
}

params = {
    "query": "modern AI laboratory",
    "per_page": 3
}

response = requests.get(
    "https://api.pexels.com/v1/search",
    headers=headers,
    params=params,
    timeout=15
)

print("Status Code:", response.status_code)

if response.status_code == 200:
    data = response.json()
    print(f"Images Found: {len(data.get('photos', []))}")

    for photo in data.get("photos", []):
        print("-" * 40)
        print("ID:", photo["id"])
        print("Photographer:", photo["photographer"])
        print("Original URL:", photo["src"]["original"])
else:
    print(response.text)