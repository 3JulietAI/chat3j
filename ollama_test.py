import requests
import json
import random

model = "dolphin2.2-mistral:latest"
template = {
  "firstName": "", 
  "lastName": "", 
  "address": {
    "street": "", 
    "city": "", 
    "state": "", 
    "zipCode": ""
  }, 
  "phoneNumber": ""
}

prompt = f"How are you today?"

data = {
    "prompt": prompt,
    "model": model,
    "format": "json",
    "stream": False,
    "options": {"temperature": 2.5, "top_p": 0.99, "top_k": 100},
}

print(f"Generating a sample user")
response = requests.post("http://localhost:11434/api/generate", json=data, stream=False)
response_text = response.text
json_data = json.loads(response_text)
print(json.dumps(json_data['response'], indent=2))