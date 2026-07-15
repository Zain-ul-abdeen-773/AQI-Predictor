import boto3
import json

def ask_claude():
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "My FastAPI app running in AWS Lambda is throwing these warnings:\n\nHopsworks unavailable: Pyarrow package not found. If you want to use Apache Arrow with Hopsworks you can install the corresponding extras via `pip install \"hopsworks[python]\"`. You can also install pyarrow directly in your environment with `pip install pyarrow`.\nhopsworks package not installed. Using local file-based feature store fallback.\nNo champion model found in registry\n\nI have `hopsworks>=3.4` in my requirements.txt. What should I change it to?"
            }
        ]
    })
    
    print("Asking Claude Opus 4.5 on AWS Bedrock...")
    try:
        response = client.invoke_model(
            modelId='us.anthropic.claude-opus-4-5-20251101-v1:0',
            body=body
        )
        response_body = json.loads(response.get('body').read())
        print("\nClaude's Response:")
        print(response_body['content'][0]['text'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ask_claude()
