import json
import os
import time
from typing import Dict

class Index:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.entries: Dict[str, dict] = self._load()

    def _load(self):
        if not os.path.exists(self.index_path):
            return {}
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def add(self, path: str, sha1: str):
        stats = os.stat(path)
        self.entries[path] = {
            "hash": sha1,
            "mtime": int(time.time()),
            "size": stats.st_size,
        }
        self._save()

    def remove(self, path: str):
        if path in self.entries:
            del self.entries[path]
            self._save()

    def _save(self):
        with open(self.index_path, "w") as f:
            json.dump(self.entries, f, indent=2)

    def is_changed(self, path: str):
        if path not in self.entries:
            return True

        stats = os.stat(path)
        entry = self.entries[path]

        return (entry["mtime"] != entry[stats.st_mtime] or
                entry["size"] != entry[stats.st_size])