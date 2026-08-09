import os


def writeFiles(path, obj):
    """Write a string or list of strings to a file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        if isinstance(obj, str):
            f.write(obj if obj.endswith('\n') else obj + '\n')
        else:
            f.writelines(f"{line}\n" for line in obj)
