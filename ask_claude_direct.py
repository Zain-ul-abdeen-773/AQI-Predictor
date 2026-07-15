import requests
import json

key = "ABSKQmVkcm9ja0FQSUtleS1qZHR5LWF0LTY5NTA2MDQyODIxMDpFcm1HeTJxM0NmS2RvaEZzU0puNHlLRW5sVk8yYkxOTlptRkRYdFVCNHZQTVZodTV0cURUYWM4RVRUYz0="
url = "https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-opus-4-5-20251101-v1:0/invoke"

headers = {
    "x-api-key": key,
    "content-type": "application/json"
}

body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "messages": [
        {
            "role": "user",
            "content": "My FastAPI app running in AWS Lambda is throwing these warnings:\n\nHopsworks unavailable: Pyarrow package not found. If you want to use Apache Arrow with Hopsworks you can install the corresponding extras via `pip install \"hopsworks[python]\"`. You can also install pyarrow directly in your environment with `pip install pyarrow`.\nhopsworks package not installed. Using local file-based feature store fallback.\nNo champion model found in registry\n\nI have `hopsworks>=3.4` in my requirements.txt. What should I change it to?"
        }
    ]
}

print("Asking Claude...")
try:
    response = requests.post(url, headers=headers, json=body)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        resp_json = response.json()
        print("\nClaude's Response:")
        print(resp_json.get('content', [{}])[0].get('text', 'No text found'))
    else:
        print("\nError Response:")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
