import smtplib
from email.mime.text import MIMEText   
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import csv
import os
from netmiko import ConnectHandler
import requests
import subprocess
import time
import re

#configuration variables
smtp_server = '10.10.10.100'
smtp_port = 1025
sender_email = 'network_monitoring@smtp.d522.wgu.internal'
recipient_email = 'stakeholders@smtp.d522.wgu.internal'
csv_file_path = '/home/student/d522-python-for-it-automation/network_devices.csv'
api_url = 'http://helpdesk.d522.wgu.internal:5000/api/tickets' 
bearer_token = 'vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE'
headers = {
    'Authorization': f'Bearer {bearer_token}',
    'Content-Type': 'application/json',    
}
os_map = {'Ubuntu': 'linux', 'VyOS': 'VyOS', 'OpenvSwitch': 'linux'}
accepted_dns = ['10.10.10.10', '10.10.10.20']
log_file = 'dns_monitoring_log'

skip_devices = ['ROUTER1', 'SMTP', 'SW1', 'SW2', 'SW3', 'SW4']

def discover_dhcp_from_router():

    try:
        router = ConnectHandler(
            device_type='vyos',
            host='10.10.10.1',
            username='vyos',
            password='vyos',
            timeout=10
        )
        
        output = router.send_command('show dhcp server leases')
        router.disconnect()

        print(f'Discovering DHCP leases from router')

        # Parse output to extract hostname and IP
        dhcp_leases = {}
        for line in output.split('\n'):
            # Look for lines with IP addresses
            if re.search(r'192\.168\.\d+\.\d+', line):
                # Extract IP and hostname
                ip_match = re.search(r'(192\.168\.\d+\.\d+)', line)
                hostname_match = re.search(r'(pc\d|svr\d|webterm-\d)', line, re.IGNORECASE)
                
                if ip_match and hostname_match:
                    ip = ip_match.group(1)
                    hostname = hostname_match.group(1).lower()
                    dhcp_leases[hostname] = ip
                    print(f'Found: {hostname} -> {ip}')
        
        return dhcp_leases
    except Exception as e:
        print(f'Error connecting to router: {e}')
        return {}

def send_email(subject, body):

    message = MIMEMultipart()
    message['from'] = sender_email
    message['to'] = recipient_email
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.sendmail(sender_email, recipient_email, message.as_string())
    server.quit()

def ticket_entry(title, description, status='open'):

    ticket_data = {
        'title': title,
        'description': description,
        'priority': 'low',
        'status': status,
        'assigned_to': 'network-team',
        'requester_email': 'dns-monitoring@smtp.d522.wgu.internal'
    }
    try:

        response = requests.post(api_url, json=ticket_data, headers=headers, verify=False)
        return response
    
    except Exception as e:
        print(f'error with {e}')
        return None

def log_status(device_name, status, message=''):

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f'[{timestamp}] {device_name}: {status} {message}\n'

    with open(log_file, 'a') as f:
        f.write(log_entry)

def remediate_dns(device_name, device_address, username, password,):

    try:
        connection = ConnectHandler(
            device_type='linux',
            host=device_address,
            username=username,
            password=password,
            timeout=10
        )

        connection.send_command('sudo sed -i "/^nameserver/d" /etc/resolv.conf')

        connection.send_command(f'sudo bash -c "echo nameserver {accepted_dns[0]} >> /etc/resolv.conf"')
        connection.send_command(f'sudo bash -c "echo nameserver {accepted_dns[1]} >> /etc/resolv.conf"')

        verify = connection.send_command('cat /etc/resolv.conf')
        print(f'Verified DNS config:\n{verify}')
                    
            
        connection.disconnect()

        return True
    except Exception as e:
        print(f' Error remediating DNS on {device_name}: {e}')
        return False

def get_current_dns(device_name, device_address, username, password):

    try:
        connection = ConnectHandler(
            device_type='linux',
            host=device_address,
            username=username,
            password=password,
            timeout=10
        )

        
        if device_name in ['SVR1', 'SVR2']:
            dns_output = connection.send_command('cat /etc/resolv.conf')
        else:
            dns_output = connection.send_command('resolvectl')

        connection.disconnect()

        return dns_output
    except Exception as e:
        return f'Error retrieving DNS: {e}'

def check_device(device):

    address = device['Device Address']

    if address == 'DHCP':
        return None

    result = subprocess.run(['ping', '-c', '2', address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def check_dns_configuaration(device):

    name = device['Device Name']
    address = device['Device Address']
    username = device['Username']
    password = device['Password']
    os_type = device['OS']

    if address == 'DHCP':
        return None

    try:
        connection = ConnectHandler(
            device_type='linux',
            host=address,
            username=username,
            password=password,
            timeout=10
        )

        try:
            dns_output = connection.send_command('resolvectl')               
        except:
            try:
                dns_output = connection.send_command('cat /etc/resolv.conf')
            except:
                pass
                
        connection.disconnect()

        #print(f'{name} DNS output: {dns_output[:100]}')

        return any(dns in dns_output for dns in accepted_dns)
    except Exception as e:
         return None

def monitor_network():
    """Main monitoring loop"""
    print('\n' + '=' * 70)
    print('NETWORK MONITOR SCAN')
    print('=' * 70 + '\n')

    with open(csv_file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        network_devices = list(csv_reader)
        print(network_devices)

        #DHCP discover
    print('Discovering DHCP IPs from router')
    dhcp_lease = discover_dhcp_from_router()

        #Update IP addresses
    for device in network_devices:
        if device['Device Address'] == 'DHCP':
            name = device['Device Name']
            name_lower = name.lower()

            if name_lower in dhcp_lease:
                device['Device Address'] = dhcp_lease[name_lower]
                print(f' Updated{name}')

    unavailable_devices = set()
    compromised_dns = set()

    while True:
        print(f'[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring system now')

        for device in network_devices:
            name = device['Device Name']
            address = device['Device Address']
            username = device['Username']
            password = device['Password']
            os_type = device['OS']

            if name in skip_devices:
                continue

#check availability
            is_available = check_device(device)

            if is_available is None:
                
                continue

            if not is_available:
                print(f' {name} ({address}) : OFFLINE')

                #send alert
                if name not in unavailable_devices:
                    unavailable_devices.add(name)

                    #send Unavailable notifcation
                    subject = f'Network Device Unavailable: {name} ({address})'
                    body = f'''Dear Network Administrator,

This is an automated notification that the following network device is currently unavailable:

Device Name: {name}
IP Address: {address}
Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please investigate this issue at your earliest convenience.

Best regards,  
Network Monitoring System'''

                    send_email(subject, body)
                    print(f' Email alert sent')

                    #create ticket
                    response = ticket_entry(
                        f'Device Unavailable - {name}',
                        f'Device {name} at {address} is currently unavailable',

                    )
                    if response:
                        print(f'Ticket created: {response.status_code}')
                    

            else:
                print(f' {name} ({address}): ONLINE')

                    #if device come back online, remove from unavailable list
                if name in unavailable_devices:
                    unavailable_devices.discard(name)

                    #dns check
                dns_ok = check_dns_configuaration(device)

                if dns_ok is None:
                    
                    continue

                if not dns_ok:
                    print(f'DNS MISCONFIGURED')


                    if name not in compromised_dns:
                        compromised_dns.add(name)
                        print(compromised_dns)

                            #get current dns settings
                        current_dns = get_current_dns(name, address, username, password)
                        except_dns = f'{accepted_dns[0]}, {accepted_dns[1]}'

                            #send dns  email alert
                        subject = f'DNS Configuration Alert: {name} ({address})'
                        body = f'''Dear Network Administrator,

This is an automated alert that the DNS configuration for the following device has been altered from the expected settings:

Device Name: {name}
IP Address: {address}
Detected DNS Setting: {current_dns}
Expected DNS Setting: {except_dns}
Time Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The system will attempt to automatically correct this configuration.

Best regards,  
Network Monitoring System'''

                        send_email(subject, body)
                        print('Email alert sent')

                        #remidiate dns
                        if remediate_dns(name, address, username, password):
                            print('DNS settings remediated')

                            #send dns corrected email
                            subject = f'DNS Configuration Corrected: {name} ({address})'
                            body = f'''Dear Network Administrator,

The DNS configuration issue previously detected on the following device has been automatically corrected:

Device Name: {name}
IP Address: {address}
Corrected DNS Setting: {except_dns}
Time Corrected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

No further action is required at this time.

Best regards,  
Network Monitoring System'''

                            send_email(subject, body)
                            print('Corrected email alert sent')

                            #create ticket
                            response = ticket_entry(
                                f'DNS is not correct - {name}',
                                f'DNS setting on  {name} at {address} are currently misconfigured. issue has been automatically remediated.',
                                status = 'resolved'
                            )
                            if response:
                                print(f'Ticket created: {response.status_code}')
                            else:
                                print('Ticket creation failed)')

                else:
                    print(f' {name} ({address}): DNS OK')

                    if name in compromised_dns:
                        compromised_dns.discard(name)

                        #log status
                    log_status(name,'OK', 'DNS correctly configured')

        print(f'Next check in 60 seconds')
        time.sleep(60)

if __name__ == '__main__':
    monitor_network()



                



        
               
