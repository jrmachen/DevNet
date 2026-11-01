import requests
import json

url = "https://swapi.info/api/planets/1"

payload = {}
headers = {
    'Content-Type': 'application/json'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.json())
