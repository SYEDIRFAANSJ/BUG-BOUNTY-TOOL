import subprocess
import json

def run(domain: str, timeout: int = 300) -> list[str]:
    result = subprocess.run(
        ['subfinder', '-d', domain, '-silent', '-json'],
        capture_output=True, text=True, timeout=timeout
    )
    subdomains = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                data = json.loads(line)
                if 'host' in data:
                    subdomains.append(data['host'])
            except json.JSONDecodeError:
                continue
    return subdomains
