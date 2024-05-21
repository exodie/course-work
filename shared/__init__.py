import os

DEFAULT_DIR_CATALOG = "/home/user/superapp/"


def format_size(size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(size) < 1024.0:
            return "%3.1f%sB" % (size, unit)
        size /= 1024.0
    return "%.1f%sB" % (size, 'Y')


def directory_size(path):
    total_size = 0
    for dir_path, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dir_path, f)
            total_size += os.path.getsize(fp)
    return format_size(total_size)
