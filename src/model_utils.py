import os
import urllib.request


def download_model(url, path, timeout=10.0, chunk_size=1024 * 1024):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response, open(
            tmp_path, "wb"
        ) as out:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp_path, path)
    except Exception as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise RuntimeError(
            f"Failed to download model from {url} to {path}: {exc}"
        ) from exc
