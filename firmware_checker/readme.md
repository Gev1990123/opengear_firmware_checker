
# Opengear Firmware Checker

A Python script to check the firmware version of Opengear ACM devices and compare it against the latest available version from the Opengear FTP server.

## Features

- Retrieves the latest firmware version from Opengear's public FTP.
- Authenticates with each device using API credentials.
- Fetches the current firmware version from each device.
- Compares device firmware with the latest available version.
- Outputs a summary of devices and whether an update is required.

## Requirements

- `Python 3.7+`
- `requests`
- `python-dotenv`
- `beautifulsoup4`

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

- Run the script:
```bash
python firmware_check.py
```
The script will print a list of devices with their current firmware version and whether an update is required.

## Output Example

```
[
  {
    "checked": "2025-10-31 14:00:00",
    "device_name": "Device1",
    "device_ip": "192.168.1.1",
    "device_firmware": "4.5.3",
    "update_required": "yes"
  },
  ...
]
```

## Notes

- SSL verification is disabled in this script to support self-signed certificates. Use with caution in production environments.
- Ensure your Opengear devices have the API enabled and are reachable from the machine running this script.
