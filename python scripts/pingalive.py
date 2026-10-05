#!/usr/bin/env python3

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def main():
    # Device connection parameters - TO BE FILLED IN
    device = {
        'device_type': 'cisco_ios',  # Change to your device type
        'host': 'x.x.x.x',  # Add IP address or hostname
        'username': 'jrmachen',  # Add username
        'password': 'xxxxxx',  # Add password
        #'secret': '',  # Add enable secret (optional)
    }

    try:
        # Connect to the device
        print(f"Connecting to {device['host']}...")
        connection = ConnectHandler(**device)
        print("Connection established successfully!")

        # Add your commands here
        # output = connection.send_command("show version")
        # print(output)

        # Close the connection
        connection.disconnect()
        print("Connection closed.")

    except NetmikoTimeoutException:
        print("Connection timeout - unable to reach the device.")
    except NetmikoAuthenticationException:
        print("Authentication failed - check username and password.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
