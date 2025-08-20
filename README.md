# FortiManager API Easy Client

A simple Python command-line application for interacting with FortiManager devices using the [pyfmg](https://github.com/p4r4n0y1ng/pyfmg) library. This tool is designed to provide a consistent user experience with the [fgt_api_easy](https://github.com/hyyperlite/fgt_api_easy) client.

## Features

- **Authentication**: Supports both API key and username/password authentication.
- **Configuration**: Load connection details from INI or JSON configuration files.
- **HTTP Methods**: Full support for `GET`, `ADD`, `SET`, `UPDATE`, `DELETE`, and `EXEC` requests.
- **Query Parameters**: Filter, format, and control API output using query parameters.
- **Data Input**: Easily send JSON data for `POST` and `PUT` requests.
- **Output Formats**: Choose between `json` (default), `pretty` (colorized JSON), and `table` formats.
- **Dynamic Tables**: Table output dynamically adjusts to the fields in the API response.
- **Customizable Tables**: Control which fields are displayed and their maximum width.
- **Error Handling**: Comprehensive error handling with specific exit codes.
- **Debug Mode**: Enable debug mode for detailed request/response logging.

## Installation

### Using Virtual Environment (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hyyperlite/fmg_api_easy.git
    cd fmg_api_easy
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The application is run via the `fmg` bash script, which is a wrapper around the `fmg_api_client.py` script.

### Command-Line Arguments

#### Connection Options
-   `-c, --config`: Path to a configuration file (INI or JSON).
-   `-i, --host, --ip`: FortiManager IP address or hostname.
-   `-u, --username`: Username (default: `admin`).
-   `-p, --password`: Password for authentication.
-   `-k, --apikey`: API key for authentication.

#### Request Options
-   `-m, --method`: HTTP method (`get`, `add`, `set`, `update`, `delete`, `exec`). **Required**.
-   `-e, --endpoint`: API endpoint path. **Required**.
-   `-d, --data`: Request data as a JSON string (for `POST`/`PUT`).
-   `-q, --query`: Query parameters (can be used multiple times).

#### Output and Formatting
-   `--format`: Output format (`json`, `pretty`, `table`). The `fmg` script defaults to `pretty`.
-   `--fields`: Comma-separated list of fields to include in the output (all formats).
-   `--table-max-width`: Maximum width for table cell content (default: 30).
-   `--table-max-fields`: Maximum number of fields to auto-detect for tables (default: 6, `0` for unlimited).

#### Additional Options
-   `--no-ssl`: Use HTTP instead of HTTPS.
-   `--verify-ssl`: Verify SSL certificates.
-   `--ssl-warnings`: Enable SSL warnings (disabled by default).
-   `--timeout`: Request timeout in seconds (default: 300).
-   `--debug`: Enable debug mode.

### Shortcut Script

The fmg_api_client.py is the main application and can be executed directly.  However, to simplify usage when using directly from the CLI a shortcut bash script "fmg" is also included.  This script simply executes fmg_api_client.py but with a shoter name and also defaults to using the output format JSON pretty which is more human readable than the default JSON format the fmg_api_client.py defaults to.  It is really just to shorten the command but has same results as you could just specify --format {json|pretty|table} in either case.

### Examples

#### 1. Get Firewall Addresses (ADOM Scope)
Get all firewall address objects from the `root` ADOM. The `fmg` script defaults to `--format pretty`.
```bash
./fmg -m get -e /pm/config/adom/root/obj/firewall/address
```

#### 2. Get Firewall Addresses (Global Scope)
Get all firewall address objects from the global configuration database.
```bash
./fmg -m get -e /pm/config/global/obj/firewall/address
```

#### 3. Create a New Firewall Address
Add a new firewall address object to the `root` ADOM using the `-d` flag.
```bash
./fmg -m add -e /pm/config/adom/root/obj/firewall/address -d '{"name": "new-address", "subnet": "10.0.0.0/24"}'
```

#### 4. Update an Existing Firewall Address
Update (set) an existing firewall address object in the global scope.
```bash
./fmg -m set -e /pm/config/global/obj/firewall/address/existing-address -d '{"subnet": "10.1.1.1/32", "comment": "Updated"}'
```

#### 5. Delete a Firewall Address
Delete a firewall address object.
```bash
./fmg -m delete -e /pm/config/adom/root/obj/firewall/address/old-address
```

#### 6. Filter Objects Based on a Condition (inside query)
Use the `filter` parameter within the `-q` flag to retrieve a subset of objects. This example filters for firewall addresses of a specific type.
```bash
./fmg -m get -e /pm/config/adom/root/obj/firewall/address -q '{"filter": ["type", "==", "ipmask"]}'
```

#### 7. Output Specific Fields from an Endpoint (API query filter)
Use the `--fields` flag to filter the response and retrieve only specific fields. This works for all output formats. This filter is an output filter, it filters from the receivied data not in the API query. (sometimes FMG returns some set of fields regardless of query filter)
```bash
./fmg -m get -e /pm/config/adom/root/obj/firewall/address '{"fields": ["name", "type", "route-tag"]}
```


#### 8. Output Specific Fields from an Endpoint (post response filter)
Use the `--fields` flag to filter the response and retrieve only specific fields. This works for all output formats. This filter is an output filter, it filters from the receivied data not in the API query.
```bash
./fmg -m get -e /pm/config/adom/root/obj/firewall/address --fields name,subnet
```


## Configuration Files

Store connection settings in a configuration file to simplify commands.

### Use a Configuration File
Use a configuration file for credentials and specify `table` format.
```bash
./fmg -c config.ini -m get -e /pm/config/adom/root/obj/firewall/address --format table
```


### INI Format (`config.ini`)
```ini
[fortimanager]
host = 10.0.0.1
username = admin
password = your_password
# apikey = your_api_key
```

### JSON Format (`config.json`)
```json
{
  "fortimanager": {
    "host": "10.0.0.1",
    "username": "admin",
    "apikey": "your_api_key"
  }
}
```

## Common FortiManager API Endpoints

-   **/pm/config/adom/{adom}/obj/firewall/address**: Firewall addresses in an ADOM.
-   **/pm/config/global/obj/firewall/address**: Global firewall addresses.
-   **/pm/config/adom/{adom}/obj/firewall/policy**: Firewall policies in an ADOM.
-   **/dvmdb/device**: Device manager database.
-   **/securityconsole/install/device/{device_name}**: Install package to a device.

## Error Handling

-   **Exit Code 0**: Success.
-   **Exit Code 1**: Configuration or validation error.
-   **Exit Code 2**: HTTP error (4xx/5xx).
-   **Exit Code 130**: Operation cancelled by user (Ctrl+C).

## Security Notes

-   **API Keys**: Prefer API keys over passwords for authentication.
-   **SSL**: Use `--verify-ssl` in production environments.
-   **Configuration Files**: Protect configuration files containing sensitive credentials.


See `fmg_api_client.py` for CLI usage details.
