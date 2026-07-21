import subprocess
import json
import tempfile
import os
import urllib.parse

def run(urls: list[str], timeout: int = 1200) -> list[dict]:
    if not urls:
        return []
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('\n'.join(urls))
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ['katana', '-list', tmp_path, '-json'],
            capture_output=True, text=True, timeout=timeout
        )
        
        endpoints = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    url = data.get('request', {}).get('endpoint', '')
                    if url:
                        parsed = urllib.parse.urlparse(url)
                        params = list(urllib.parse.parse_qs(parsed.query).keys())
                        endpoints.append({
                            'url': url,
                            'method': data.get('request', {}).get('method', 'GET'),
                            'params': params
                        })
                except json.JSONDecodeError:
                    continue
        return endpoints
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
