#!/usr/bin/env python3
"""
FortiManager API Client

A simple command-line interface for interacting with FortiManager devices using the pyfmg library.
Supports authentication via API key or username/password, and can read configuration from a file.
"""

import argparse
import json
import sys
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List
import warnings
import os

# Disable SSL warnings by default unless explicitly enabled
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from pyFMG.fortimgr import FortiManager, FMGBaseException, FMGValidSessionException, FMGValueError, FMGResponseNotFormedCorrect, FMGConnectionError, FMGConnectTimeout
except ImportError:
    print("Error: pyfmg package not found. Please install it using: pip install pyfmg")
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    print("Error: tabulate package not found. Please install it using: pip install tabulate")
    sys.exit(1)

class TableFormatter:
    """Dynamically formats FortiManager API responses as tables"""
    @staticmethod
    def format_table(response_data: Dict[str, Any], max_fields: int = 6, max_width: int = 50) -> str:
        # Try to extract a list of items from the response
        if isinstance(response_data, dict):
            data_list = response_data.get('results') or response_data.get('data') or response_data.get('items')
            if isinstance(data_list, list):
                pass
            elif isinstance(data_list, dict):
                data_list = [data_list]
            else:
                data_list = [response_data]
        elif isinstance(response_data, list):
            data_list = response_data
        else:
            return f"Table format not supported for response type: {type(response_data)}"

        if not data_list:
            return "No data to display in table format"

        # Auto-detect fields
        field_counts = {}
        for item in data_list[:10]:
            if isinstance(item, dict):
                for key in item.keys():
                    field_counts[key] = field_counts.get(key, 0) + 1
        common_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)
        fields = [field[0] for field in common_fields[:max_fields]]
        if not fields:
            return "No suitable fields found for table display"

        # Prepare table data
        headers = fields
        rows = []
        for item in data_list:
            row = []
            for field in fields:
                value = item.get(field, "-")
                formatted_value = TableFormatter._flatten_value(value)
                if max_width and len(formatted_value) > max_width:
                    formatted_value = formatted_value[:max_width-3] + "..."
                row.append(formatted_value)
            rows.append(row)
        table = tabulate(rows, headers=headers, tablefmt="grid", stralign="left")
        summary = f"{len(data_list)} result(s) found"
        return f"{summary}\n{table}"

    @staticmethod
    def _flatten_value(value: Any) -> str:
        if value is None:
            return "-"
        elif isinstance(value, (list, tuple)):
            if not value:
                return "-"
            if isinstance(value[0], dict) and 'name' in value[0]:
                return ", ".join([str(item.get('name', '')) for item in value])
            return ", ".join([str(item) for item in value])
        elif isinstance(value, dict):
            if 'name' in value:
                return str(value['name'])
            elif len(value) == 1:
                return str(list(value.values())[0])
            else:
                return str(value)
        else:
            return str(value)

class FortiManagerAPIClient:
    """FortiManager API Client wrapper class"""
    def __init__(self, host: str, username: Optional[str] = None, password: Optional[str] = None,
                 apikey: Optional[str] = None, use_ssl: bool = True, verify_ssl: bool = False,
                 timeout: int = 300, debug: bool = False):
        self.host = host
        self.username = username or "admin"
        self.password = password
        self.apikey = apikey
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.debug = debug
        if not apikey and not password:
            raise ValueError("Either password or apikey must be provided")
    def _create_connection(self) -> FortiManager:
        kwargs = {
            'debug': self.debug,
            'use_ssl': self.use_ssl,
            'verify_ssl': self.verify_ssl,
            'timeout': self.timeout
        }
        if self.apikey:
            kwargs['apikey'] = self.apikey
            return FortiManager(self.host, self.username, **kwargs)
        else:
            return FortiManager(self.host, self.username, self.password, **kwargs)
    def execute_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
                       query_params: Optional[List[str]] = None) -> tuple[int, Dict[str, Any]]:
        method = method.lower()
        if method not in ['get', 'add', 'set', 'update', 'delete', 'exec']:
            raise ValueError(f"Unsupported HTTP method: {method}")
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        try:
            with self._create_connection() as fmg:
                args = query_params or []
                kwargs = data or {}
                if method == 'get':
                    return fmg.get(endpoint, *args)
                elif method == 'add':
                    return fmg.add(endpoint, *args, **kwargs)
                elif method in ['set', 'update']:
                    return fmg.update(endpoint, *args, **kwargs)
                elif method == 'delete':
                    return fmg.delete(endpoint, *args)
                elif method == 'exec':
                    return fmg.execute(endpoint, *args, **kwargs)
                else:
                    return -5, {"error": "Unsupported method", "details": f"Method {method} not supported"}
        except (FMGConnectionError, FMGConnectTimeout) as e:
            print(f"Connection error: {e}")
            return -1, {"error": "Connection failed", "details": str(e)}
        except FMGValidSessionException as e:
            print(f"Session error: {e}")
            return -2, {"error": "Invalid session", "details": str(e)}
        except FMGBaseException as e:
            print(f"FortiManager API error: {e}")
            return -3, {"error": "API error", "details": str(e)}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return -4, {"error": "Unexpected error", "details": str(e)}

def load_config_file(config_path: str) -> Dict[str, str]:
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    config = {}
    try:
        with open(config_file, 'r') as f:
            json_config = json.load(f)
            if 'fortimanager' in json_config:
                config = json_config['fortimanager']
            else:
                config = json_config
        return config
    except json.JSONDecodeError:
        pass
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        section = 'fortimanager' if 'fortimanager' in parser else 'DEFAULT'
        config = dict(parser[section])
        return config
    except Exception as e:
        raise ValueError(f"Unable to parse configuration file: {e}")

def parse_data_argument(data_str: str) -> Dict[str, Any]:
    try:
        return json.loads(data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="FortiManager API Client - Simple CLI for FortiManager JSON API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get all firewall address objects from the 'root' ADOM
  %(prog)s -m get -e /pm/config/adom/root/obj/firewall/address

  # Get all firewall address objects from the Global scope
  %(prog)s -m get -e /pm/config/global/obj/firewall/address

  # Add a new firewall address to the 'root' ADOM
  %(prog)s -m add -e /pm/config/adom/root/obj/firewall/address -d '{"name": "new-address", "subnet": "10.0.0.0/24"}'

  # Update (set) an existing firewall address in the Global scope
  %(prog)s -m set -e /pm/config/global/obj/firewall/address/existing-address -d '{"subnet": "10.1.1.1/32", "comment": "Updated"}'

  # Delete a firewall address object
  %(prog)s -m delete -e /pm/config/adom/root/obj/firewall/address/old-address

  # Execute a script on a device
  %(prog)s -m exec -e /dvmdb/adom/root/script/execute -d '{"adom": "root", "scope": [{"name": "MyDevice", "vdom": "root"}], "script": "MyTestScript"}'

Configuration file format (INI):
  [fortimanager]
  host = 10.0.0.1
  username = admin
  password = your_password

Configuration file format (JSON):
  {
    "fortimanager": {
      "host": "10.0.0.1",
      "username": "admin",
      "apikey": "your_api_key"
    }
  }
""")
    conn_group = parser.add_argument_group('Connection')
    conn_group.add_argument('-c', '--config', metavar='FILE', help='Configuration file path (INI or JSON format)')
    conn_group.add_argument('-i', '--host', '--ip', metavar='HOST', help='FortiManager IP address or hostname')
    conn_group.add_argument('-u', '--username', metavar='USER', default='admin', help='Username (default: admin)')
    conn_group.add_argument('-p', '--password', metavar='PASS', help='Password for authentication')
    conn_group.add_argument('-k', '--apikey', metavar='KEY', help='API key for authentication')
    req_group = parser.add_argument_group('Request')
    req_group.add_argument('-m', '--method', required=True, choices=['get', 'add', 'set', 'update', 'delete', 'exec'], help='API method to use')
    req_group.add_argument('-e', '--endpoint', required=True, metavar='PATH', help='API endpoint path (e.g., /pm/config/adom/root/obj/firewall/address)')
    req_group.add_argument('-d', '--data', metavar='JSON', help='Request data as JSON string (for POST/PUT)')
    req_group.add_argument('-q', '--query', metavar='PARAM', action='append', help='Query parameters (can be used multiple times)')
    opt_group = parser.add_argument_group('Options')
    opt_group.add_argument('--no-ssl', action='store_true', help='Use HTTP instead of HTTPS')
    opt_group.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificates')
    opt_group.add_argument('--ssl-warnings', action='store_true', help='Enable SSL warnings (disabled by default)')
    opt_group.add_argument('--timeout', type=int, default=300, metavar='SEC', help='Request timeout in seconds (default: 300)')
    opt_group.add_argument('--debug', action='store_true', help='Enable debug mode')
    opt_group.add_argument('--format', choices=['json', 'pretty', 'table'], default='json',
                          help='Output format (default: json)')
    table_group = parser.add_argument_group('Table Options')
    table_group.add_argument('--table-max-width', type=int, default=50, metavar='WIDTH', help='Maximum width for table cell content (default: 50)')
    table_group.add_argument('--table-max-fields', type=int, default=6, metavar='NUM', help='Maximum number of fields to auto-detect for table display (default: 6, set to 0 for unlimited)')
    args = parser.parse_args()
    config = {}
    if args.config:
        try:
            config = load_config_file(args.config)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            sys.exit(1)
    if args.ssl_warnings:
        warnings.resetwarnings()
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    host = args.host or config.get('host') or config.get('ip')
    username = args.username or config.get('username', 'admin')
    password = args.password or config.get('password')
    apikey = args.apikey or config.get('apikey')
    if not host:
        print("Error: FortiManager host/IP address is required", file=sys.stderr)
        sys.exit(1)
    if not apikey and not password:
        print("Error: Either API key or password is required", file=sys.stderr)
        sys.exit(1)
    request_data = None
    if args.data:
        try:
            request_data = parse_data_argument(args.data)
        except ValueError as e:
            print(f"Error parsing data: {e}", file=sys.stderr)
            sys.exit(1)
    try:
        client = FortiManagerAPIClient(
            host=host,
            username=username,
            password=password,
            apikey=apikey,
            use_ssl=not args.no_ssl,
            verify_ssl=args.verify_ssl,
            timeout=args.timeout,
            debug=args.debug
        )
        status_code, response = client.execute_request(
            method=args.method,
            endpoint=args.endpoint,
            data=request_data,
            query_params=args.query
        )
        print(f"Status Code: {status_code}")
        if args.format == 'table':
            try:
                table_output = TableFormatter.format_table(
                    response,
                    max_fields=args.table_max_fields if args.table_max_fields != 0 else 999,
                    max_width=args.table_max_width
                )
                print(table_output)
            except Exception as e:
                print(f"Error formatting table: {e}", file=sys.stderr)
                print("Falling back to JSON output:")
                print(json.dumps(response, indent=2, default=str))
        elif args.format == 'json':
            print(f"Response: {json.dumps(response, default=str)}")
        else:
            print("Response:")
            print(json.dumps(response, indent=2, default=str))
        if isinstance(status_code, int):
            if status_code < 0:
                sys.exit(1)
            elif status_code >= 400:
                sys.exit(2)
        elif isinstance(status_code, str):
            if status_code.lower() not in ['success', 'ok']:
                print(f"Warning: Unexpected status code: {status_code}", file=sys.stderr)
                sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)

if __name__ == '__main__':
    main()
