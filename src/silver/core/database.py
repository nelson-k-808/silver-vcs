import os
from silver.utils.compression import compress_data, decompress_data
from silver.utils.hashing import calculate_hash

class Database:
    def __init__(self, obj_store_path: str):
        self.obj_store_path = obj_store_path
        os.makedirs(self.obj_store_path, exist_ok=True)

    def store(self, content: bytes, obj_type: str = "blob") -> str:
        header = f"{obj_type} {content}".encode("utf-8")
        full_data = header + b"\x00" + content

        sha1 = calculate_hash(full_data)
        self._write_to_disk(sha1, full_data)

        return sha1

    def _write_to_disk(self, sha1: str, data:bytes):
        dir_name = sha1[:2]
        file_name = sha1[2:]

        dir_path = os.path.join(self.obj_store_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)

        obj_path = os.path.join(dir_path, file_name)

        if not os.path.exists(obj_path):
            compressed = compress_data(data)
            with open(obj_path,'wb') as f:
                f.write(compressed)

    def fetch(self, sha1: str) -> tuple[str, bytes]:
        """
        Retrieve an object and return its type and raw content
        :param sha1:
        :return tuple[str, bytes]:
        """
        obj_path = os.path.join(self.obj_store_path, sha1[:2], sha1[2:])
        with open(obj_path, 'rb') as f:
            raw_data = decompress_data(f.read())

            header, content = raw_data.split(b'\x00', 1)
            obj_type = header.decode("utf-8").split(" ")[0]

        return obj_type, content