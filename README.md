# OS2IoT-Editor
Dash-based bulk editor for OS2IoT devices with CSV upload, change preview and safe PUT updates via API.

## What this project is
A small Dash-based web application that allows safe bulk updating of devices in OS2IoT via CSV upload.

The application:

- Uploads a CSV file containing device updates

- Fetches current device data from the OS2IoT API

- Compares name, location and metadata

- Generates a full change preview

- Builds a PUT payload

- Requires explicit confirmation before applying updates

- The tool is designed as a controlled and transparent bulk-edit solution for OS2IoT device management.

## Requirements
Python 3.9+

pip packages: dash, dash-bootstrap-components, pandas, requests, python-dotenv

Powershell: python -m pip install dash dash-bootstrap-components pandas requests python-dotenv

## Environment variables (.env)
Create a .env file in the same folder as the script:

os2iot_BASE_URL=https://your-os2iot-api/devices

os2iot_api=YOUR_API_KEY

- os2iot_BASE_URL must point directly to the device endpoint (without trailing slash).

- os2iot_api must be a valid API key with GET and PUT permissions.

- The application will fail if these variables are missing.

## Expected CSV format
The CSV file must contain the following columns:

name,id,latitude,longitude,metadata

Example:

name,id,latitude,longitude,metadata
Temperature Sensor A,123,56.1629,10.2039,"{""floor"": ""2""}"
Humidity Sensor B,124,56.1700,10.2100,

- id must match an existing OS2IoT device ID.

- latitude and longitude must be numeric.

- metadata must contain valid JSON or be empty.

- If metadata contains invalid JSON, existing metadata will be retained.

- Coordinates are compared using float tolerance (1e-9) to avoid false changes due to rounding.

## How to run
From PowerShell in the project folder:

# (optional) create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
python -m pip install dash dash-bootstrap-components pandas requests python-dotenv

# run the application
python app.py

The browser will automatically open at: http://127.0.0.1:8050

## Application workflow
1. Upload CSV

The application reads the file and displays filename and number of rows.

2. Generate preview

For each row in the CSV:

The current device is fetched via GET request.

The following fields are compared: Name, Latitude, Longitude., Metadata (parsed and compared as JSON object)

Each row is marked:

- Ændres (Will be updated)

- Ingen ændring (No update needed)

A summary header shows how many devices will be changed.

3. Inspect payload

You can open a modal window to inspect the exact PUT payload before execution.

4. Confirm changes

A confirmation dialog appears: Er du sikker på at du vil ændre X enheder?

No updates are executed without confirmation.

5. Execute updates

Each changed device is updated individually using: PUT {BASE_URL}/{device_id}

The application displays:

- Number of successful updates

- List of failed device IDs with status codes

## Safety design
- No automatic updates

- Explicit preview required

- Explicit confirmation required

- Only changed devices are updated

- Per-device error handling

- Metadata validated and parsed as JSON

- Float tolerance prevents false GPS changes

This ensures controlled and transparent bulk modifications.


## Quick troubleshooting
401 / 403

- Verify API key

- Verify permissions

404

- Verify device ID

- Verify BASE_URL endpoint

Metadata not updating

- Ensure valid JSON format

- Ensure proper escaping of quotes in CSV

Application does not open automatically

- Open manually in browser: http://127.0.0.1:8050

## Author
[Lasse Østergaard — LinkedIn](https://www.linkedin.com/in/lasse-%C3%B8stergaard-9b70bb136/), februar 2026, iotlab@aarhus.dk
