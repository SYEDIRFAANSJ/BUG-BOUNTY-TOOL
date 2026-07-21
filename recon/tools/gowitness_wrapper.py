import subprocess
import tempfile
import os

def run(urls: list[str], timeout: int = 900) -> dict:
    if not urls:
        return {}
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('\n'.join(urls))
        tmp_path = tmp.name

    out_dir = tempfile.mkdtemp()
    screenshots = {}
    
    try:
        subprocess.run(
            ['gowitness', 'file', '-f', tmp_path, '--destination', out_dir],
            capture_output=True, text=True, timeout=timeout
        )
        
        for filename in os.listdir(out_dir):
            if filename.endswith('.png'):
                # Simple mapping heuristic
                url = filename.replace('.png', '').replace('-', '://', 1)
                screenshots[url] = os.path.join(out_dir, filename)
                
        return screenshots
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        # Images should be moved in pipeline before deleting out_dir
