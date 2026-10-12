from argparse import ArgumentParser
from getpass import getpass
from ncclient import manager
import xml.dom.minidom


def main() -> None:
    parser = ArgumentParser(description="Retrieve a device's running configuration.")
    parser.add_argument("host", nargs="?", default="10.10.20.48",
                        help="Device IP address or DNS name (default: 10.10.20.48)")
    parser.add_argument("-u", "--username", default="developer",
                        help="NETCONF username (default: developer)")
    parser.add_argument("-p", "--password", help="NETCONF password (prompted if omitted)")
    parser.add_argument("--port", type=int, default=830,
                        help="NETCONF port (default: 830)")
    args = parser.parse_args()
    password = args.password or getpass("NETCONF password: ")

    native_filter = '''
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native"/>
    '''

    with manager.connect(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
        hostkey_verify=False,
        device_params={"name": "csr"},
    ) as connection:
        response = connection.get_config(
            source="running",
            filter=("subtree", native_filter),
        )

    xml_dom = xml.dom.minidom.parseString(response.xml)
    print(xml_dom.toprettyxml(indent="  "))


if __name__ == "__main__":
    main()
