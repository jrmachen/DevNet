from ncclient import manager
import xmltodict
import sys
from typing import Dict, Any
import xml.dom.minidom

# NETCONF filter for interface information
INTERFACE_FILTER = '''
<filter>
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
            <name/>
            <description/>
            <enabled/>
            <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                <address>
                    <ip/>
                    <netmask/>
                </address>
            </ipv4>
        </interface>
    </interfaces>
</filter>
'''

LOOPBACK_CONFIG = '''
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
            <name>Loopback10</name>
            <description>Configured by setloop.py</description>
            <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
            <enabled>true</enabled>
        </interface>
    </interfaces>
</config>
'''

def connect_to_device(host: str, username: str, password: str, port: int = 830) -> manager.Manager:
    """
    Establishes a NETCONF connection to the device.
    """
    try:
        connection = manager.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            device_params={'name': 'csr'}
        )
        return connection
    except Exception as e:
        print(f"Failed to connect to {host}: {str(e)}")
        raise

def configure_loopback(connection: manager.Manager) -> None:
    """
    Creates or updates Loopback10 and enables it.
    """
    try:
        # Send Configureation to the device
        response = connection.edit_config(target='running', config=LOOPBACK_CONFIG)

        # Pretty print the response
        print("\nConfiguration Result:")
        print(xml.dom.minidom.parseString(response.xml).toprettyxml())

        if response.ok:
            print("\nLoopback10 interface configured successfully!")
        else:
            print("\nFailed to configure Loopback10 interface")

    except Exception as e:
        print(f"Error configuring interface: {str(e)}")
        raise


def main():
    # Device connection parameters
    device = {
        'host': '10.10.20.48',  # Replace with your device's IP
        'username': 'developer',     # Replace with your username
        'password': 'C1sco12345',     # Replace with your password
        'port': 830             # Standard NETCONF port
    }

    try:
        # Connect to the device
        with connect_to_device(**device) as conn:
            print(f"Successfully connected to {device['host']}")

            #configure the loopback interface
            configure_loopback(conn)
    except Exception as e:
        print(f"script execution failed: {str(e)}")
        sys.exit(1)
if __name__=="__main__":
    main()