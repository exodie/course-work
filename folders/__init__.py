import os

from System.shared import DEFAULT_DIR_CATALOG


def create_trash():
    trash_path = os.path.join(DEFAULT_DIR_CATALOG, 'Корзина')
    if not os.path.exists(trash_path):
        os.makedirs(trash_path)


def create_logs():
    logs_path = os.path.join(DEFAULT_DIR_CATALOG, 'logs')
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)


def create_system_folder():
    system_path = os.path.join(DEFAULT_DIR_CATALOG, 'System')
    if not os.path.exists(system_path):
        os.makedirs(system_path)
        open(os.path.join(system_path, 'placeholder.txt'), 'a').close()


def create_initial_folders():
    initial_folders = ['folder1', 'folder2']
    for folder in initial_folders:
        folder_path = os.path.join(DEFAULT_DIR_CATALOG, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
