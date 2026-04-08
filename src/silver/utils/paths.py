import os
from typing import Optional

def find_silver_root(start_path: str = ".") -> Optional[str]:
    """
    Recursively climb up the directory looking for .silver folder.
    Returns the absolute path to the project root or None if not found.
    :param start_path:
    :return:
    """
    current_dir = os.path.abspath(start_path)
    while True:
        if os.path.isdir(os.path.join(current_dir, ".silver")):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    return None

