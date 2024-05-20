import requests
import json

# Define the API endpoint
endpoint = "http://192.168.1.25:11434/api/chat"

# Define the payload
payload = {
    "model": "llama3",
    "messages": [
        {
            "role": "user",
            "content": "why is the sky blue?"
        }
    ]
}

# Define the headers
headers = {
    "Content-Type": "application/json"
}

# Send a POST request to the API
response = requests.post(endpoint, json=payload, headers=headers, stream=True)

# Check if the request was successful
if response.status_code == 200:
    # Iterate through the stream of JSON objects
    for line in response.iter_lines():
        # Decode the JSON object
        if line:
            json_object = line.decode('utf-8')
            data = json.loads(json_object)
            
            # Extract and print the content immediately
            message_content = data.get("message", {}).get("content", "")
            print(message_content, end='', flush=True)  # Print without newline and flush the output
else:
    print("Request failed with status code:", response.status_code)
