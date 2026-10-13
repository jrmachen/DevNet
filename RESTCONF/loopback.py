import requests
import json
import urllib3

# Suppress SSL certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Device connection details
HOST = "10.10.20.48"
PORT = 443
USER = "developer"
PASSWORD = "C1sco12345"

# RESTCONF endpoint for Loopback22 interface
INTERFACE_NAME = "Loopback22"
IP_ADDRESS = "22.22.22.22"
NETMASK = "255.255.255.255"

URL = f"https://{HOST}:{PORT}/restconf/data/ietf-interfaces:interfaces/interface={INTERFACE_NAME}"

# RESTCONF headers
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# Payload defining the loopback interface using IETF YANG model
PAYLOAD = {
    "ietf-interfaces:interface": {
        "name": INTERFACE_NAME,
        "description": "Configured via RESTCONF",
        "type": "iana-if-type:softwareLoopback",
        "enabled": True,
        "ietf-ip:ipv4": {
            "address": [
                {
                    "ip": IP_ADDRESS,
                    "netmask": NETMASK
                }
            ]
        }
    }
}


def create_loopback():
    """Create or update the loopback interface using HTTP PUT (RESTCONF)."""
    print(f"Configuring {INTERFACE_NAME} ({IP_ADDRESS}/{NETMASK}) on {HOST} via RESTCONF...")

    try:
        response = requests.put(
            URL,
            auth=(USER, PASSWORD),
            headers=HEADERS,
            data=json.dumps(PAYLOAD),
            verify=False,
            timeout=10
        )

        if response.status_code in [200, 201, 204]:
            print(f"Success! {INTERFACE_NAME} configured with HTTP status code: {response.status_code}")
        else:
            print(f"Failed to configure interface. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return False

    return True


def get_loopback():
    """Retrieve and display the loopback interface details via RESTCONF."""
    print(f"\nVerifying {INTERFACE_NAME} configuration via RESTCONF GET...")

    try:
        response = requests.get(
            URL,
            auth=(USER, PASSWORD),
            headers={"Accept": "application/yang-data+json"},
            verify=False,
            timeout=10
        )

        if response.status_code == 200:
            print("Current interface configuration:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Unable to retrieve interface. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Connection error during verification: {e}")


def main():
    if create_loopback():
        get_loopback()


if __name__ == "__main__":
    main()
