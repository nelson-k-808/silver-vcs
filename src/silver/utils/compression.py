import zlib

def compress_data(data: bytes) -> bytes:
    return zlib.compress(data)

def decompress_data(data: bytes) -> bytes:
    return zlib.decompress(data)