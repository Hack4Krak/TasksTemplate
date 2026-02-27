from pathlib import Path

from xxhash import xxh64


def hash_file(path: Path, chunk_size=8192):
    buffer = xxh64()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            buffer.update(chunk)

    return buffer.hexdigest()
