from pathlib import Path

from xxhash import xxh64


def hash_file(path: Path, chunk_size=8192):
    buf = xxh64()

    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            buf.update(chunk)

    return buf.hexdigest()
