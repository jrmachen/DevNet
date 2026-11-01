import subprocess
import time
from datetime import datetime

import requests

from getdata import HEADERS, HOST, PASSWORD, PORT, USER


URL = f"https://{HOST}:{PORT}/restconf/data/ietf-interfaces:interfaces"
POLL_INTERVAL = 30
REQUEST_TIMEOUT = 10
PING_TIMEOUT = 5


def device_is_alive():
    try:
        result = subprocess.run(
            ["ping", "-c", "1", HOST],
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def fetch_interfaces():
    response = requests.get(
        URL,
        auth=(USER, PASSWORD),
        headers=HEADERS,
        verify=False,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("RESTCONF response is not a JSON object")

    interfaces_data = data.get("ietf-interfaces:interfaces", data.get("interfaces", {}))
    if not isinstance(interfaces_data, dict):
        raise ValueError("RESTCONF response does not contain interface data")

    interfaces = interfaces_data.get("interface", [])
    if isinstance(interfaces, dict):
        interfaces = [interfaces]
    if not isinstance(interfaces, list):
        raise ValueError("RESTCONF response does not contain an interface list")

    snapshot = {}
    for index, interface in enumerate(interfaces):
        if not isinstance(interface, dict):
            raise ValueError("RESTCONF response contains an invalid interface")

        name = str(interface.get("name") or f"unknown-{index}")
        ipv4_data = interface.get("ietf-ip:ipv4", interface.get("ipv4", {}))
        if not isinstance(ipv4_data, dict):
            raise ValueError(f"RESTCONF response contains invalid IPv4 data for {name}")

        addresses = ipv4_data.get("address", [])
        if isinstance(addresses, dict):
            addresses = [addresses]
        if not isinstance(addresses, list):
            raise ValueError(f"RESTCONF response contains an invalid address list for {name}")

        ipv4_addresses = tuple(sorted(
            f"{address['ip']}/{address['prefix-length']}"
            if address.get("prefix-length") is not None
            else str(address["ip"])
            for address in addresses
            if isinstance(address, dict) and address.get("ip")
        ))
        snapshot[name] = {
            "enabled": interface.get("enabled", False),
            "type": interface.get("type", "unknown"),
            "ipv4_addresses": ipv4_addresses,
        }

    return snapshot


def is_loopback(name):
    return name.lower().startswith("loopback")


def describe_interface(interface):
    addresses = ", ".join(interface["ipv4_addresses"]) or "none"
    return (
        f"enabled={interface['enabled']}, type={interface['type']}, "
        f"IPv4={addresses}"
    )


def print_interface_brief(interfaces):
    rows = []
    for name, interface in interfaces.items():
        addresses = interface["ipv4_addresses"]
        ip_address = addresses[0].split("/", 1)[0] if addresses else "unassigned"
        enabled = interface["enabled"]
        status = "up" if enabled else "administratively down"
        protocol = "up" if enabled else "down"
        rows.append((name, ip_address, status, protocol))

    columns = ("Interface", "IP-Address", "Status", "Protocol")
    widths = [
        max(len(columns[index]), max((len(row[index]) for row in rows), default=0))
        for index in range(len(columns))
    ]
    print("IP interface brief:")
    print("  ".join(column.ljust(widths[index]) for index, column in enumerate(columns)))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def print_changes(previous, current):
    added = current.keys() - previous.keys()
    removed = previous.keys() - current.keys()
    changed = {
        name for name in current.keys() & previous.keys()
        if current[name] != previous[name]
    }
    ordered_names = sorted(
        added | removed | changed,
        key=lambda name: (not is_loopback(name), name.lower()),
    )
    added_order = [name for name in ordered_names if name in added]
    removed_order = [name for name in ordered_names if name in removed]
    changed_order = [name for name in ordered_names if name in changed]

    if not added and not removed and not changed:
        print("No interface changes detected.")
        return

    for name in added_order:
        label = "LOOPBACK ADDED" if is_loopback(name) else "ADDED"
        print(f"[{label}] {name}: {describe_interface(current[name])}")

    for name in removed_order:
        label = "LOOPBACK REMOVED" if is_loopback(name) else "REMOVED"
        print(f"[{label}] {name}: {describe_interface(previous[name])}")

    for name in changed_order:
        label = "LOOPBACK CHANGED" if is_loopback(name) else "CHANGED"
        print(f"[{label}] {name}:")
        for field in ("enabled", "type", "ipv4_addresses"):
            old_value = previous[name][field]
            new_value = current[name][field]
            if old_value != new_value:
                print(f"  {field}: {old_value} -> {new_value}")


def monitor_interfaces():
    previous = None
    while True:
        poll_started = time.monotonic()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Checking {HOST}...")

        if device_is_alive():
            print("ICMP ping succeeded.")
        else:
            print("ICMP ping failed; checking RESTCONF anyway (ICMP may be blocked).")

        try:
            current = fetch_interfaces()
        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"Unable to retrieve interfaces via RESTCONF: {error}")
        else:
            print("Device is reachable via RESTCONF.")
            print_interface_brief(current)
            if previous is None:
                loopbacks = [name for name in current if is_loopback(name)]
                print(
                    f"Initial snapshot loaded: {len(current)} interfaces, "
                    f"{len(loopbacks)} loopbacks."
                )
                previous = current
            else:
                print_changes(previous, current)
                previous = current

        elapsed = time.monotonic() - poll_started
        time.sleep(max(0, POLL_INTERVAL - elapsed))


if __name__ == "__main__":
    try:
        monitor_interfaces()
    except KeyboardInterrupt:
        print("\nInterface monitoring stopped.")