import getpass
import os

import xmltodict
from ncclient import manager


HOST = "devnetsandboxiosxec8k.cisco.com"
INTERFACE_FILTER = """
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
        <name/>
        <enabled/>
        <oper-status/>
        <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
            <address>
                <ip/>
            </address>
        </ipv4>
    </interface>
</interfaces>
"""
INTERFACE_STATE_FILTER = """
<interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
        <name/>
        <oper-status/>
    </interface>
</interfaces-state>
"""


def get_interfaces(connection):
    """Retrieve operational interface details from the device."""
    response = connection.get(filter=("subtree", INTERFACE_FILTER))
    response_data = xmltodict.parse(response.xml)

    state_response = connection.get(filter=("subtree", INTERFACE_STATE_FILTER))
    state_data = xmltodict.parse(state_response.xml)
    state_interfaces = (
        state_data.get("rpc-reply", {})
        .get("data", {})
        .get("interfaces-state", {})
        .get("interface", [])
    )
    if not isinstance(state_interfaces, list):
        state_interfaces = [state_interfaces]
    operational_status = {
        interface["name"]: interface.get("oper-status", "unknown")
        for interface in state_interfaces
        if isinstance(interface, dict) and "name" in interface
    }

    interfaces = (
        response_data.get("rpc-reply", {})
        .get("data", {})
        .get("interfaces", {})
        .get("interface", [])
    )
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    for interface in interfaces:
        if isinstance(interface, dict):
            interface["oper-status"] = operational_status.get(
                interface.get("name"), interface.get("oper-status", "unknown")
            )

    return response_data


def display_interfaces(response_data):
    """Print interface data in a format similar to ``show ip int brief``."""
    try:
        interfaces = response_data["rpc-reply"]["data"]["interfaces"]["interface"]
    except (KeyError, TypeError):
        print("No interface data was returned by the device.")
        return

    if not isinstance(interfaces, list):
        interfaces = [interfaces]

    print(f"{'Interface':<20}{'IP-Address':<18}{'Status':<12}{'Protocol'}")
    print("-" * 62)

    for interface in interfaces:
        name = interface.get("name", "N/A")
        enabled = str(interface.get("enabled", "false")).lower() == "true"
        status = "up" if enabled else "down"
        protocol = "up" if str(interface.get("oper-status", "")).lower() == "up" else "down"

        ip_address = "unassigned"
        ipv4 = interface.get("ipv4", {})
        addresses = ipv4.get("address", []) if isinstance(ipv4, dict) else []
        if not isinstance(addresses, list):
            addresses = [addresses]
        if addresses:
            ip_address = addresses[0].get("ip", ip_address)

        print(f"{name:<20}{ip_address:<18}{status:<12}{protocol}")


def main():
    username = os.environ.get("NETCONF_USERNAME", "jmache6")
    password = os.environ.get("NETCONF_PASSWORD")
    if not password:
        password = getpass.getpass(f"NETCONF password for {username}: ")

    try:
        with manager.connect(
            host=HOST,
            port=830,
            username=username,
            password=password,
            hostkey_verify=False,
            device_params={"name": "csr"},
            timeout=30,
        ) as connection:
            display_interfaces(get_interfaces(connection))
    except Exception as error:
        print(f"NETCONF request to {HOST} failed: {error}")


if __name__ == "__main__":
    main()