import argparse
import json
from urllib.parse import quote

import requests
import urllib3

from getdata import HOST, PASSWORD, PORT, USER


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INTERFACES_URL = f"https://{HOST}:{PORT}/restconf/data/ietf-interfaces:interfaces"
LOOPBACK_NAME = "Loopback11"
LOOPBACK_IP = "11.11.11.11"
LOOPBACK_NETMASK = "255.255.255.255"
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}


def interface_url(interface_name):
    encoded_name = quote(interface_name, safe="")
    return f"{INTERFACES_URL}/interface={encoded_name}"


def get_interfaces():
    response = requests.get(
        INTERFACES_URL,
        auth=(USER, PASSWORD),
        headers={"Accept": "application/yang-data+json"},
        verify=False,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    interfaces_data = data.get("ietf-interfaces:interfaces", data.get("interfaces", {}))
    interfaces = interfaces_data.get("interface", [])
    if isinstance(interfaces, dict):
        interfaces = [interfaces]
    return {interface["name"]: interface for interface in interfaces if "name" in interface}


def create_loopback():
    payload = {
        "ietf-interfaces:interface": {
            "name": LOOPBACK_NAME,
            "description": "Configured via RESTCONF",
            "type": "iana-if-type:softwareLoopback",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [{"ip": LOOPBACK_IP, "netmask": LOOPBACK_NETMASK}]
            },
        }
    }
    response = requests.put(
        interface_url(LOOPBACK_NAME),
        auth=(USER, PASSWORD),
        headers=HEADERS,
        data=json.dumps(payload),
        verify=False,
        timeout=10,
    )
    response.raise_for_status()
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"Unexpected loopback response: HTTP {response.status_code}")
    print(f"Configured {LOOPBACK_NAME} with {LOOPBACK_IP}/32.")


def disable_interface(interface_name):
    payload = {"ietf-interfaces:interface": {"enabled": False}}
    response = requests.patch(
        interface_url(interface_name),
        auth=(USER, PASSWORD),
        headers=HEADERS,
        data=json.dumps(payload),
        verify=False,
        timeout=10,
    )
    response.raise_for_status()
    print(f"Administratively shut {interface_name} (HTTP {response.status_code}).")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create Loopback11 and optionally shut only explicitly selected interfaces. "
            "No interfaces are shut unless named with --disable."
        )
    )
    parser.add_argument(
        "--disable",
        action="append",
        default=[],
        metavar="NAME",
        help="interface to shut; repeat this option for each interface",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply changes; without this option, show a dry run",
    )
    args = parser.parse_args()

    selected_names = list(dict.fromkeys(args.disable))
    if LOOPBACK_NAME in selected_names:
        parser.error(f"{LOOPBACK_NAME} is the requested new loopback and cannot be shut by this script")

    try:
        interfaces = get_interfaces()
    except (requests.exceptions.RequestException, ValueError) as error:
        parser.exit(1, f"Unable to retrieve interfaces from {HOST}: {error}\n")

    missing_names = [name for name in selected_names if name not in interfaces]
    if missing_names:
        parser.error("unknown interface name(s): " + ", ".join(missing_names))

    active_names = []
    for name in selected_names:
        enabled = interfaces[name].get("enabled")
        if enabled is True:
            active_names.append(name)
        elif enabled is False:
            print(f"Skipping {name}: already administratively down.")
        else:
            parser.error(f"cannot determine whether {name} is enabled; refusing to change it")

    print(f"Target device: {HOST}")
    print(f"Create/update: {LOOPBACK_NAME} ({LOOPBACK_IP}/32), enabled")
    if active_names:
        print("Shut explicitly selected interfaces: " + ", ".join(active_names))
    else:
        print("No interface shutdowns selected.")

    if not args.apply:
        print("Dry run only; pass --apply and confirm to make changes.")
        return

    confirmation = input("Type APPLY to continue: ")
    if confirmation != "APPLY":
        print("No changes made.")
        return

    try:
        create_loopback()
        for name in active_names:
            disable_interface(name)
    except (requests.exceptions.RequestException, RuntimeError) as error:
        parser.exit(1, f"Configuration failed; earlier changes may already have been applied: {error}\n")


if __name__ == "__main__":
    main()