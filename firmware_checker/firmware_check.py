import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re

load_dotenv()

# Disable SSL warnings (optional, but useful for self-signed certs)
requests.packages.urllib3.disable_warnings()

# Credentials
username = os.getenv("UNAME")
password = os.getenv("PWORD")

def latest_version():
    url = "https://ftp.opengear.com/download/opengear_appliances/ACM/current/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    firmware_versions = []
    for link in soup.find_all('a', href=True):
        match = re.search(r'acm700x-(\d+\.\d+\.\d+)\.flash', link['href'])
        if match:
            firmware_versions.append(match.group(1))

    latest_version = sorted(firmware_versions, key=lambda v: list(map(int, v.split('.'))))[-1]
    return latest_version

# Read devices from file
with open('device_details.txt', 'r') as file: 
    devices = [line.strip().split(",") for line in file.readlines()[1:]]
    

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
device_firmware = []
latest_firmware = latest_version()

for name, ip in devices:
    print(f'Checking {name}, {ip}....')
    try: 
        # Authenticate
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

    # Get Firmware Version
    headers = { "Authorization": f"Token {token}" }
    version_url = f"https://{ip}/api/v1.8/system/version"

    try:
        version_response = requests.get(version_url, headers=headers, verify=False)
        version_response.raise_for_status()
        version_info = version_response.json()
        firmware_version = version_info.get("system_version", {}).get("firmware_version")

        if firmware_version == latest_firmware:
            update_required = 'no'
        elif firmware_version < latest_firmware:
            update_required = 'yes'

        device_firmware.append({
            'checked': timestamp,
            'device_name': name,
            'device_ip': ip,
            'device_firmware': firmware_version,
            'update_required': update_required
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

print(device_firmware)


