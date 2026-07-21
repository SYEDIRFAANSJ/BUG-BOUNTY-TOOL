import re
import urllib.request

def extract_from_js(js_urls: list[str]) -> list[dict]:
    pattern = re.compile(r'(?:"|\')(((?:[a-zA-Z]{1,10}://|/)[^"\'\s]+|([a-zA-Z0-9_\-]+/)+[a-zA-Z0-9_\-]+))(?:"|\')')
    endpoints = []
    
    for url in js_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                matches = pattern.findall(content)
                for match in matches:
                    endpoints.append({
                        'url': match[0],
                        'method': 'GET',
                        'discovered_via': 'js_parse'
                    })
        except Exception:
            continue
            
    return endpoints
