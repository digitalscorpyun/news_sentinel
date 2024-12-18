import filetype

def what(file_path):
    kind = filetype.guess(file_path)
    if kind is None:
        return None
    return kind.extension
