from sys import api_version

import requests
import json

base_url = "https://swapi.info/playground"
endpoint = "people/"

response = requests.get(base_url + endpoint)

print(response.text)
