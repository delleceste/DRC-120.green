#!/usr/bin/env python3
"""Read-only inspection of a running REW REST API; changes no measurements."""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:4735')
    parser.add_argument('--output', type=Path, default=Path('analysis/api-probe'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    endpoints = ['/doc.json', '/application', '/measurements',
                 '/measurements/commands', '/measurements/process-commands',
                 '/measurements/arithmetic-functions',
                 '/measurements/impulse-response/units']
    results = {}
    errors = {}
    for endpoint in endpoints:
        try:
            with urlopen(args.url.rstrip('/') + endpoint, timeout=15) as response:
                raw = response.read().decode('utf-8')
            value = json.loads(raw)
            results[endpoint] = value
            filename = endpoint.strip('/').replace('/', '_')
            if not filename.endswith('.json'):
                filename += '.json'
            (args.output / filename).write_text(json.dumps(value, indent=2) + '\n')
            print(f'OK {endpoint}', flush=True)
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            errors[endpoint] = str(error)
            print(f'FAILED {endpoint}: {error}', flush=True)
            if isinstance(error, URLError) and not isinstance(error, HTTPError):
                break
    (args.output / 'status.json').write_text(json.dumps({
        'url': args.url, 'successful_endpoints': list(results), 'errors': errors
    }, indent=2) + '\n')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
