import os

def writeFiles(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        if isinstance(obj, str):
            f.write(f"{obj}\n")
        else:
            for line in obj:
                f.write(f"{line}\n")
#Add other file types and merge the same here...
#Make sure to cover all file writes here