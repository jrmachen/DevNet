import argparse
import getpass
import os
import sys
import warnings

import xmltodict
from ncclient import manager


HOST = "devnetsandboxiosxec9k.cisco.com"
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


def get_interfaces(connection):
    """Retrieve operational interface details from the device."""
    response = connection.get(filter=("subtree", INTERFACE_FILTER))
    return xmltodict.parse(response.xml)


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
    parser = argparse.ArgumentParser(
        description="Display interface status from a NETCONF-enabled IOS XE device."
    )
    parser.add_argument(
        "host",
        nargs="?",
        default=os.environ.get("NETCONF_HOST", HOST),
        help=f"Device IP address or DNS name (default: {HOST})",
    )
    parser.add_argument(
        "-u",
        "--username",
        default=os.environ.get("NETCONF_USERNAME", "jmache6"),
        help="NETCONF username (default: jmache6)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("NETCONF_PORT", "830")),
        help="NETCONF-over-SSH port (default: 830)",
    )
    args = parser.parse_args()

    password = os.environ.get("NETCONF_PASSWORD")
    if not password:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                password = getpass.getpass(f"NETCONF password for {args.username}: ")
        except getpass.GetPassWarning:
            print(
                "No secure terminal is available for the password prompt. "
                "Run this script from a terminal that supports hidden input.",
                file=sys.stderr,
            )
            return 1

    try:
        with manager.connect(
            host=args.host,
            port=args.port,
            username=args.username,
            password=password,
            hostkey_verify=False,
            device_params={"name": "iosxe"},
            timeout=30,
        ) as connection:
            display_interfaces(get_interfaces(connection))
    except Exception as error:
        print(
            f"NETCONF request to {args.host}:{args.port} failed: {error}",
            file=sys.stderr,
        )
        if args.port == 830 and "SSH protocol banner" in str(error):
            print(
                "The host reset the connection before SSH/NETCONF started. "
                "Confirm NETCONF is enabled and port 830 is exposed. "
                "If the host is configured to offer the NETCONF SSH subsystem "
                "on port 22, try --port 22; shell SSH access alone does not "
                "guarantee that NETCONF is available.",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())