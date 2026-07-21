import subprocess
import json
import tempfile
import os

def run(subdomains: list[str], timeout: int = 600) -> list[dict]:
    if not subdomains:
        return []
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('\n'.join(subdomains))
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ['httpx', '-l', tmp_path, '-json', '-tech-detect', '-status-code', '-title'],
            capture_output=True, text=True, timeout=timeout
        )
        
        results = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    results.append({
                        'url': data.get('url'),
                        'status_code': data.get('status_code'),
                        'tech': data.get('tech', []),
                        'title': data.get('title'),
                        'is_live': 'status_code' in data
                    })
                except json.JSONDecodeError:
                    continue
        return results
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
