import subprocess
import urllib.parse

def run(domain: str, timeout: int = 600) -> list[dict]:
    try:
        result = subprocess.run(
            ['gau', domain],
            capture_output=True, text=True, timeout=timeout
        )
        
        endpoints = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parsed = urllib.parse.urlparse(line)
                params = list(urllib.parse.parse_qs(parsed.query).keys())
                endpoints.append({
                    'url': line,
                    'method': 'GET',
                    'params': params
                })
        return endpoints
    except Exception:
        return []
