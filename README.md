# FortiManager API Generic Client

A simple Python command-line application for interacting with FortiManager devices using the [pyfmg](https://github.com/p4r4n0y1ng/pyfmg) library.

## Features

- Support for both API key and username/password authentication
- Configuration file support (INI and JSON formats)
- All HTTP methods (GET, POST, PUT, DELETE)
- Query parameter support for filtering and formatting
- JSON data input for POST/PUT requests
- Multiple output formats: JSON, pretty JSON, and table
- Table output with automatic field detection for any FortiManager object
- Customizable table fields and formatting
- Comprehensive error handling
- Debug mode support

## Installation

### Option 1: Using Virtual Environment (Recommended)

1. Clone or download this repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv fmg_api_env
   source fmg_api_env/bin/activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: System Python

```bash
pip install pyfmg requests tabulate
```

## Usage

The client provides a flexible command-line interface for interacting with the FortiManager API.

### Examples

**1. Get all firewall address objects from the 'root' ADOM:**
```bash
./fmg -m get -e /pm/config/adom/root/obj/firewall/address
```

**2. Get all firewall address objects from the Global scope:**
```bash
./fmg -m get -e /pm/config/global/obj/firewall/address
```

**3. Add a new firewall address to the 'root' ADOM:**
```bash
./fmg -m post -e /pm/config/adom/root/obj/firewall/address -d '{"name": "new-address", "subnet": "10.0.0.0/24"}'
```

**4. Update (set) an existing firewall address in the Global scope:**
```bash
./fmg -m put -e /pm/config/global/obj/firewall/address/existing-address -d '{"subnet": "10.1.1.1/32", "comment": "Updated"}'
```

**5. Use a configuration file for credentials:**
```bash
./fmg -c config.ini -m get -e /pm/config/adom/root/obj/firewall/address
```

### Configuration File

You can store connection details in an INI or JSON file to avoid passing them on the command line.

**INI format (`config.ini`):**
```ini
[fortimanager]
host = 10.0.0.1
username = admin
password = your_password
```

**JSON format (`config.json`):**
```json
{
  "fortimanager": {
    "host": "10.0.0.1",
    "username": "admin",
    "apikey": "your_api_key"
  }
}
```

See `fmg_api_client.py` for CLI usage details.
