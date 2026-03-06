
# Opengear Firmware Checker ABC

A Python script to check and optionally upgrade the firmware version of Opengear ACM700x devices by comparing against the latest or a specified version from Opengear’s public FTP archive.

## Features

- Retrieves the latest firmware version from Opengear's public FTP.
- Optionally upgrades devices to a specified firmware version using --version.
- Authenticates with each device using API credentials.
- Fetches the current firmware version from each device.
- Compares device firmware with the target version.
- Uploads and installs firmware via SSH if an upgrade is required.
- Backs up device configuration before upgrade.
- Cleans up old backup files.
- Waits for device reboot and confirms upgrade success.
- Outputs a summary of devices and upgrade status.

## Requirements

- `Python 3.7+`
- `requests`
- `python-dotenv`
- `beautifulsoup4`
- `netmiko`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Setup

- Create a .env file using the .env.example file
- Edit the .env 
- Create a device_details.txt file with the following format:
<pre>
name,ip
device1,192.168.1.1
</pre>

## Usage

- Check and upgrade to the latest firmware:
```bash
python firmware_check.py
```

- Check and upgrade to a specific firmware version:
```bash
python firmware_check.py --version 5.2.3
```

## Output Example

```
[
  {
    "checked": "2025-10-31 14:00:00",
    "device_name": "Device1",
    "device_ip": "192.168.1.1",
    "device_firmware": "4.5.3",
    "update_required": "yes",
    "upgrade_result": "success"
  },
  {
    "checked": "2025-10-31 14:00:00",
    "device_name": "Device2",
    "device_ip": "192.168.1.2",
    "device_firmware": "5.2.4",
    "update_required": "no",
    "upgrade_result": "skipped"
  }
]
```

## Notes

- SSL verification is disabled in this script to support self-signed certificates. Use with caution in production environments.
- Ensure your Opengear devices have the API enabled and are reachable from the machine running this script.
- Firmware files are downloaded from Opengear’s archive and cached locally to avoid repeated downloads.
- During firmware upgrades, the device will reboot, which may cause the SSH session to close unexpectedly. This is normal behavior and is handled gracefully by the script.