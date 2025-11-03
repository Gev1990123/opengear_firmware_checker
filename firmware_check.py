import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re
from netmiko import ConnectHandler, file_transfer
import time
import socket
import argparse

load_dotenv()

# Disable SSL warnings (optional, but useful for self-signed certs)
requests.packages.urllib3.disable_warnings()

# Credentials
username = os.getenv("UNAME")
password = os.getenv("PWORD")
secret = os.getenv("SECRET")

parser = argparse.ArgumentParser(description="Opengear ACM700x Firmware Upgrade Tool")
parser.add_argument("--version", type=str, help="Specify the firmware version to upgrade to (e.g., 5.2.3). If omitted, the latest version will be used.")
args = parser.parse_args()

def latest_version():
    url = "https://ftp.opengear.com/download/opengear_appliances/ACM/current/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    firmware_versions = []
    for link in soup.find_all('a', href=True):
        match = re.search(r'acm700x-(\d+\.\d+\.\d+)\.flash', link['href'])
        if match:
            firmware_versions.append(match.group(1))

    if firmware_versions:
        return sorted(firmware_versions, key=lambda v: list(map(int, v.split('.'))))[-1]
    else:
        raise ValueError("No firmware versions found.")


def upload_and_upgrade(host, username, password, firmware_path, filename):

    device = {
        "device_type": "linux",
        "host": host,
        "username": username,
        "password": password,
        "secret": secret
    }

    print(f'Connecting to {host}')

    conn = ConnectHandler(**device)
    conn.enable()

    print(f"Uploading filename {filename} to /tmp on {host}")
    transfer_result = file_transfer(conn, source_file=firmware_path, dest_file=f"{filename}", file_system="/tmp", direction="put", overwrite_file=True)
    print("Transfer Result:", transfer_result)

    print(f"Running firmware upgrade on {host}")
    cmd = f"sudo netflash -l /tmp/{filename}"
    output = conn.send_command_timing(cmd, delay_factor=5)

    if "password" in output.lower():
        output += conn.send_command_timing(f"{password}\n", delay_factor=5)

    if "Are you sure" in output:
        output += conn.send_command_timing("y", delay_factor=5)

    print(output)
    conn.disconnect()

    print(f"Upgrade triggered on {host}, waiting for reboot...")
    if wait_for_reboot(host):
        #version = verify_upgrade(host, username, password)
        print(f"{host} successfully upgraded to firmware.")
        return 'success'
    else:
        print(f"Timeout waiting for {host} to come back online")
        return 'failed'


def wait_for_reboot(host, timeout=600):
    print(f"Waiting up to {timeout//60} minutes for host to reboot...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            socket.create_connection((host, 22), timeout=5)
            print(f"{host} is back online.")
            return True
        except Exception:
            time.sleep(10)
    return False

def get_firmware(version):
    url = f"https://ftp.opengear.com/download/opengear_appliances/ACM/archive/{version}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    firmware_versions = []
    for link in soup.find_all('a', href=True):
        match = re.search(r'(acm700x-(\d+\.\d+\.\d+)\.flash)', link['href'])
        if match:
            firmware_versions.append((match.group(2), match.group(1)))
    
    if not firmware_versions:
        raise ValueError(f"No firmware found for version {version}")

    selected = sorted(firmware_versions, key=lambda v: list(map(int, v[0].split('.'))))[-1]
    firmware_url = f"{url}/{selected[1]}"
    print(firmware_url)
    filename = selected[1]
    
    firmware_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(firmware_path):
        print(f"Downloading firmware {filename}...")
        fw_data = requests.get(firmware_url)
        with open(firmware_path, 'wb') as f:
            f.write(fw_data.content)
        print("Download complete.")

    return firmware_path, filename

# Read devices from file
with open('device_details.txt', 'r') as file: 
    devices = [line.strip().split(",") for line in file.readlines()[1:]]
    
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
device_firmware = []

selected_version = args.version if args.version else latest_version()
firmware_path, filename = get_firmware(selected_version)

for name, ip in devices:
    print(f'Checking {name}, {ip}....')
    try: 
        auth_url = f"https://{ip}/api/v1.8/sessions"
        payload = {"username": username,"password": password}
        response = requests.post(auth_url, data=json.dumps(payload), verify=False)
        response.raise_for_status()
        token = response.json().get("session")
    except requests.exceptions.RequestException as e:
        device_firmware.append({
            'checked': timestamp,
            'device_name': name,
            'device_ip': ip,
            'device_firmware': 'Authentication Failed',
            'update_required': 'unknown'
        })
        continue

    headers = { "Authorization": f"Token {token}" }
    version_url = f"https://{ip}/api/v1.8/system/version"

    try:
        version_response = requests.get(version_url, headers=headers, verify=False)
        version_response.raise_for_status()
        version_info = version_response.json()
        firmware_version = version_info.get("system_version", {}).get("firmware_version")

        update_required = 'yes' if firmware_version != selected_version else 'no'

        result = None
        if update_required == 'yes':
            result = upload_and_upgrade(ip, username, password, firmware_path, filename)

        device_firmware.append({
            'checked': timestamp,
            'device-name': name,
            'device_ip': ip,
            'device_firmware': firmware_version,
            'update_required': update_required,
            'upgrade_result': result if result else 'skipped'
        })

    except requests.exceptions.RequestException as e:
        device_firmware.append({
            'checked': timestamp,
            'device_name': name,
            'device_ip': ip,
            'device_firmware': 'Failed to retrieve firmware version',
            'update_required': 'unknown'
        })
        print(f"Failed to retrieve firmware version from {ip}: {e}")

print(json.dumps(device_firmware, indent=2))