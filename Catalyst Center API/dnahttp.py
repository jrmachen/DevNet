import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL certificate warnings if connecting to sandboxes with self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://sandboxdnac.cisco.com"
AUTH_ENDPOINT = "/dna/system/api/v1/auth/token"
USERNAME = "devnetuser"
PASSWORD = "Cisco123!"

def get_auth_token(base_url, username, password):
    """
    Authenticates with Cisco Catalyst Center (DNA Center) and returns the auth token.
    """
    url = f"{base_url}{AUTH_ENDPOINT}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(username, password),
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        token = response.json().get("Token")
        print("Successfully obtained authentication token.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return None

def main():
    # Step 1: Obtain and hold the authentication token
    token = get_auth_token(BASE_URL, USERNAME, PASSWORD)

    if not token:
        print("Unable to proceed without a valid token.")
        return

    # Step 2: Use the token in headers for subsequent requests
    headers = {
        "X-Auth-Token": token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Example subsequent request: Retrieve network devices
    devices_url = f"{BASE_URL}/dna/intent/api/v1/network-device"
    print(f"\nMaking subsequent request to: {devices_url}")
    
    try:
        response = requests.get(devices_url, headers=headers, verify=False)
        response.raise_for_status()
        devices_data = response.json()
        print(f"Request successful! Response received with {len(devices_data.get('response', []))} device(s).")
    except requests.exceptions.RequestException as e:
        print(f"Subsequent request failed: {e}")

if __name__ == "__main__":
    main()
