import boto3
import json
import sys

def ask_claude(prompt):
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    
    try:
        response = client.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=body
        )
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    prompt = """
    I have a Lambda function for my FastAPI app. 
    It is throwing these warnings in CloudWatch:
    Hopsworks unavailable: Pyarrow package not found. If you want to use Apache Arrow with Hopsworks you can install the corresponding extras via `pip install "hopsworks[python]"`. You can also install pyarrow directly in your environment with `pip install pyarrow`.
    hopsworks package not installed. Using local file-based feature store fallback.
    No champion model found in registry
    Local feature store not found at /app/data/feature_store
    
    What should I do?
    """
    print(ask_claude(prompt))
