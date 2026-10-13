import requests
from argparse import ArgumentParser
from getpass import getpass


def main():

    parser = ArgumentParser(description='Retrieve hardware inventory from one or more devices.')

    # Input parameters
    parser.add_argument('-hosts', '--hosts', type=str, default='10.10.20.48',
                        help="Comma-separated device addresses (default: 10.10.20.48)")
    parser.add_argument('-user', '--username', type=str, default='developer',
                        help="NETCONF/RESTCONF username (default: developer)")
    parser.add_argument('-passwd', '--password', type=str,
                        help="Device password (prompted if omitted)")

    args = parser.parse_args()
    password = args.password or getpass('Device password: ')
    url = 'https://{}/restconf/data/Cisco-IOS-XE-device-hardware-oper:device-hardware-data/device-hardware'
    inv_cache = {}

    hosts = args.hosts.split(',')

    for host in hosts:

        u = url.format(host)

        headers = {
            'Accept': "application/yang-data+json",
        }

        response = None

        try:
            response = requests.request('GET', u, auth=(
                args.username, password), headers=headers, verify=False)
            response.raise_for_status()
        except Exception as e:
            print('Failed to get inventory from device: {}'.format(e))
            continue

        inv = response.json()

        for asset in inv['Cisco-IOS-XE-device-hardware-oper:device-hardware']['device-inventory']:
            if host not in inv_cache:
                inv_cache[host] = []

            if asset['serial-number'] == '':
                continue

            inv_cache[host].append(
                {'sn': asset['serial-number'], 'pn': asset['part-number']})

    for host, comps in inv_cache.items():
        print('Host {} serial numbers:'.format(host))
        for comp in comps:
            print('\t{}'.format(comp['sn']))


if __name__ == '__main__':
    main()