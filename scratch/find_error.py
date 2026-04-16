import os

def find_string(root_dir, target):
    for root, dirs, files in os.walk(root_dir):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if target in line:
                            print(f"Found in {path}:{i}: {line.strip()}")
            except Exception as e:
                pass

if __name__ == "__main__":
    find_string(".", "ClientConnector")
