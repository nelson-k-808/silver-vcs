import os
from src.silver.core.database import Database

class Workspace:
    """
    Workspace class acts as a scanner that recursively translates a directory into a
    nested hierarchy of Tree and blob hashes

    files/blbbs are represented as 100644
    directories/trees are represented as 040000

    Return's a tree object's hash
    """
    def __init__(self, db: Database, ignored_list: list[str] = None):
        self.db = db
        self.ignored_list = ignored_list

    def build_tree(self, current_path: str="") -> str:
        entries = []
        for name in sorted(os.listdir(current_path)):
            if name in self.ignored_list:
                continue

            full_path = os.path.join(current_path, name)

            if os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    blob_hash = self.db.store(f.read(), obj_type="blob")
                    entries.append(f"100644 blob {blob_hash} {name}")
            elif os.path.isdir(full_path):
                tree_hash = self.build_tree(full_path)
                entries.append(f"040000 tree {tree_hash} {name}")

        # Create the Tree object for this level
        tree_content = "\n".join(entries).encode("utf-8")

        return self.db.store(tree_content, obj_type="tree")