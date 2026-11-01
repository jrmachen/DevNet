import json
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST = "devnetsandboxiosxec8k.cisco.com"
PORT = 443
USER = "jmache6"
PASSWORD = "56b5Up&WBL4iL$V"

HEADERS = {
    "Accept": "application/yang-data+json",
}

SYSTEM_PATHS = [
    "ietf-system:system",
    "ietf-system:system-state",
    "Cisco-IOS-XE-device-hardware-oper:device-hardware-data",
    "Cisco-IOS-XE-platform-oper:components",
]


def get_resource(path):
    """GET a RESTCONF data resource and print the JSON (or error)."""
    url = f"https://{HOST}:{PORT}/restconf/data/{path}"
    print(f"\nGetting {path} from {HOST} via RESTCONF...")

    try:
        response = requests.get(
            url,
            auth=(USER, PASSWORD),
            headers=HEADERS,
            verify=False,
            timeout=15,
        )

        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Unable to retrieve {path}. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")


def get_system_info():
    """Retrieve and display system information via RESTCONF."""
    print(f"Gathering system information from {HOST}...")
    for path in SYSTEM_PATHS:
        get_resource(path)


if __name__ == "__main__":
    get_system_info()
