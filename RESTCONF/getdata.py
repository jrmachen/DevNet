import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST = "devnetsandboxiosxec8k.cisco.com"
PORT = 443
USER = "jmache6"
PASSWORD = "56b5Up&WBL4iL$V"

URL = f"https://{HOST}:{PORT}/restconf/data/ietf-interfaces:interfaces"

HEADERS = {
    "Accept": "application/yang-data+json",
}


def print_interface_brief(data):
    interfaces_data = data.get("ietf-interfaces:interfaces", data.get("interfaces", {}))
    interfaces = interfaces_data.get("interface", [])
    if isinstance(interfaces, dict):
        interfaces = [interfaces]

    rows = []
    for interface in interfaces:
        ip_data = interface.get("ietf-ip:ipv4", interface.get("ipv4", {}))
        addresses = ip_data.get("address", [])
        if isinstance(addresses, dict):
            addresses = [addresses]
        ip_address = next(
            (address["ip"] for address in addresses if address.get("ip")),
            "unassigned",
        )

        enabled = interface.get("enabled", False)
        status = "up" if enabled else "administratively down"
        protocol = "up" if enabled else "down"
        rows.append((interface.get("name", "unknown"), ip_address, status, protocol))

    columns = ("Interface", "IP-Address", "Status", "Protocol")
    widths = [
        max(len(columns[index]), max((len(row[index]) for row in rows), default=0))
        for index in range(len(columns))
    ]
    print("Interface brief:")
    print("  ".join(column.ljust(widths[index]) for index, column in enumerate(columns)))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def get_interfaces():
    """Retrieve and display interface details via RESTCONF."""
    print(f"Getting interface details from {HOST} via RESTCONF...")

    try:
        response = requests.get(
            URL,
            auth=(USER, PASSWORD),
            headers=HEADERS,
            verify=False,
            timeout=10,
        )

        if response.status_code == 200:
            print_interface_brief(response.json())
        else:
            print(f"Unable to retrieve interfaces. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    get_interfaces()
