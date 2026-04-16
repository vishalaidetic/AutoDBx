import os

def list_subdirectories(path: str) -> list[str]:
    """
    Lists all direct subdirectories in the given path.
    Returns a list of directory names.
    """
    if not os.path.isdir(path):
        raise ValueError(f"Path is not a valid directory: {path}")
    
    subdirs = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            subdirs.append(item)
    return subdirs

