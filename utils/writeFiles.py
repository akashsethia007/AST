import os

def writeSTFiles(path, st_list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file = open(path, 'w')
    headers = list(st_list[0].keys())
    file.write(','.join(headers)+"\n")
    for row in st_list:
        values = [str(row.get(header, "")) for header in headers]
        file.write(",".join(values) + "\n")
    file.close()
#Add other file types and merge the same here...
#Make sure to cover all file writes here