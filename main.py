
import shutil
import sys
import os
import subprocess
import logging
import psutil
import pyudev

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget, QAction,
    QMenu, QMessageBox, QInputDialog, QFileSystemModel, QLineEdit, QPushButton, QToolBar, QShortcut,
    QTextEdit
)
from PyQt5.QtCore import QModelIndex, Qt, QFileInfo
from PyQt5.QtGui import QKeySequence

from System.folders import create_trash, create_system_folder, create_initial_folders, create_logs
from System.logs import LogFileDialog, create_logs_with_msg
from System.queue import send_message
from System.shared import DEFAULT_DIR_CATALOG, directory_size
from System.tasks import TasksDialog
from System.terminal import TerminalWindow


class CustomFileSystemModel(QFileSystemModel):
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.column() == 1:
            file_info = QFileInfo(self.filePath(index))
            if file_info.isDir():
                return directory_size(file_info.absoluteFilePath())
        return super().data(index, role)


logging.basicConfig(filename='../superapp.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SuperApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.observer = None
        self.monitor = None
        self.udev_context = None
        self.log_widget = None
        self.terminal = None
        self.terminalButton = None
        self.timer = None
        self.searchButton = None
        self.searchInput = None
        self.tree = None
        self.model = None
        self.contextMenu = None
        self.clipboard_path: str | None = None
        self.original_paths = {}
        self.processListWidget = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Суперапп-0.9')
        self.setGeometry(100, 100, 800, 600)

        create_trash()
        create_system_folder()
        create_initial_folders()
        create_logs()

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('Файл')
        tasks_menu = main_menu.addMenu('Задачи')
        applications_menu = main_menu.addMenu('Приложения')
        about_menu = main_menu.addMenu('Справка')

        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about_info)
        shortcut_action = QAction("Горячие клавиши", self)
        shortcut_action.triggered.connect(self.show_shortcuts)
        about_menu.addAction(about_action)
        about_menu.addAction(shortcut_action)

        show_all_tasks_action = QAction('Открыть все задания', self)
        show_all_tasks_action.triggered.connect(self.show_all_tasks)
        tasks_menu.addAction(show_all_tasks_action)

        open_terminal_action = QAction('Системный терминал', self)
        open_terminal_action.triggered.connect(self.open_system_terminal)
        open_browser_action = QAction('Браузер', self)
        open_browser_action.triggered.connect(self.open_system_browser)
        open_system_monitor_action = QAction('Системный монитор', self)
        open_system_monitor_action.triggered.connect(self.open_system_monitor)
        open_calculator_action = QAction('Калькулятор', self)
        open_calculator_action.triggered.connect(self.open_system_calculator)
        applications_menu.addAction(open_browser_action)
        applications_menu.addAction(open_terminal_action)
        applications_menu.addAction(open_system_monitor_action)
        applications_menu.addAction(open_calculator_action)

        create_root_folder_action = QAction('Создать папку в корневой', self)
        create_root_folder_action.triggered.connect(self.create_root_folder)
        create_root_file_action = QAction('Создать файл в корневой', self)
        create_root_file_action.triggered.connect(self.create_root_file)

        file_menu.addAction(create_root_folder_action)
        file_menu.addAction(create_root_file_action)

        self.contextMenu = QMenu(self)

        self.model = CustomFileSystemModel()
        self.model.setRootPath(DEFAULT_DIR_CATALOG)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(DEFAULT_DIR_CATALOG))
        self.tree.setContextMenuPolicy(3)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        layout = QVBoxLayout()
        layout.addWidget(self.tree)

        toolbar = QToolBar("Поиск объектов")
        self.addToolBar(Qt.RightToolBarArea, toolbar)

        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("Поиск по имени файла")
        toolbar.addWidget(self.searchInput)

        self.searchButton = QPushButton("Поиск")
        toolbar.addWidget(self.searchButton)
        self.searchButton.clicked.connect(self.search_item)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.clipboard_path = None

        delete_shortcut = QShortcut(QKeySequence.Delete, self)
        delete_shortcut.activated.connect(self.delete_item)

        ctrl_delete_shortcut = QShortcut(QKeySequence("Ctrl+Delete"), self)
        ctrl_delete_shortcut.activated.connect(self.delete_immediately_item)

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_item)

        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.paste_item)

        create_file_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        create_file_shortcut.activated.connect(self.create_file_item)

        create_folder_shortcut = QShortcut(QKeySequence("Ctrl + Shift + N"), self)
        create_folder_shortcut.activated.connect(self.create_folder_item)

        open_terminal_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Alt+T"), self)
        open_terminal_shortcut.activated.connect(self.open_terminal)

        rename_file_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        rename_file_shortcut.activated.connect(self.rename_item)

        recovery_file_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        recovery_file_shortcut.activated.connect(self.restore_item)

        self.setAcceptDrops(True)
        self.tree.setDragEnabled(True)

        self.log_widget = QTextEdit()
        layout.addWidget(self.log_widget)

        select_log_button = QPushButton("Выбрать лог-файл")
        select_log_button.clicked.connect(self.select_log_file)
        layout.addWidget(select_log_button)

        self.update_processes("APP|RUN", "Application is started", "../logs/actions.log")

        self.terminalButton = QPushButton("Терминал")
        toolbar.addWidget(self.terminalButton)
        self.terminalButton.clicked.connect(self.open_terminal)

        self.udev_context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.udev_context)
        self.monitor.filter_by(subsystem='block')
        self.observer = pyudev.MonitorObserver(self.monitor, self.handle_device_event)
        self.observer.start()

    def show_all_tasks(self):
        all_processes = list(psutil.process_iter())
        user_processes = [p for p in all_processes if p.username() != 'root']

        users_info = subprocess.check_output(["w"]).decode("utf-8")
        user_processes_count = len(user_processes)
        total_processes_count = len(all_processes)

        add_tasks = {
            "Количество пользовательских процессов:": f"{user_processes_count}",
            "Всего процессов:": f"{total_processes_count}"
        }

        dialog = TasksDialog(add_tasks, users_info, self)
        dialog.exec_()

    def handle_device_event(self, action, device):
        if action == 'add' and 'ID_FS_TYPE' in device:
            device_path = device.device_node
            device_name = device['ID_FS_LABEL'] if 'ID_FS_LABEL' in device else os.path.basename(device_path)

            if device_name not in self.original_paths:
                self.original_paths[device_name] = device_path

                # Получаем абсолютный путь к каталогу приложения
                app_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # Создаем новый каталог для устройства внутри каталога вашего приложения
                device_directory = os.path.join(app_directory, device_name)
                os.makedirs(device_directory, exist_ok=True)

                # Устанавливаем созданный каталог как корневой для модели
                self.model.setRootPath(device_directory)

                print(f"Подключено устройство: {device_name} ({device_path})")

        elif action == 'remove':
            for name, path in list(self.original_paths.items()):
                if path == device.device_node:
                    del self.original_paths[name]

                    # Удаляем каталог для устройства
                    app_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    device_directory = os.path.join(app_directory, name)
                    shutil.rmtree(device_directory, ignore_errors=True)

                    print(f"Отключено устройство: {name} ({path})")
                    break

    def remove_device_from_tree(self, device_name):
        root_path = self.model.rootPath()

        if root_path.endswith(device_name):
            new_root_path = os.path.dirname(root_path)
            self.model.setRootPath(new_root_path)

            self.tree.setRootIndex(self.model.index(new_root_path))

            queue_message = f"REMOVE_DEVICE|{device_name}"
            log_message = f"Device {device_name} successfully disconnected."
            log_path = "../logs/actions.log"

            self.update_processes(queue_message, log_message, log_path)

    def update_processes(self, queue_message, log_message, log_path):
        self.log_widget.append(log_message)
        create_logs_with_msg(log_message, log_path)
        send_message(queue_message)

    def select_log_file(self):
        dialog = LogFileDialog()
        if dialog.exec_():
            log_file_path = dialog.get_file_path()
            if not os.path.exists(os.path.dirname(log_file_path)):
                os.makedirs(os.path.dirname(log_file_path))
            with open(log_file_path, 'r') as file:
                self.log_widget.setText(file.read())

    def copy_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        if file_path:
            if file_path.endswith('/System') or file_path.endswith('/Корзина'):
                QMessageBox.warning(self, 'Ошибка', 'Эту папку нельзя скопировать!')
                return

            self.clipboard_path = file_path

            queue_message = f"MOVE_FILE|{file_path}"
            log_message = f"Файл {os.path.basename(file_path)} успешно скопирован."
            log_path = "../logs/actions.log"

            self.update_processes(queue_message, log_message, log_path)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не выбран элемент для копирования!')

    def paste_item(self):
        if not self.clipboard_path:
            QMessageBox.warning(self, 'Ошибка', 'Нечего вставлять!')
            return

        destination_folder = self.model.filePath(self.tree.currentIndex())

        if not os.path.isdir(destination_folder):
            QMessageBox.warning(self, 'Ошибка', 'Выберите папку для вставки!')
            return

        destination_path = os.path.join(destination_folder, os.path.basename(self.clipboard_path))

        if os.path.exists(destination_path):
            QMessageBox.warning(self, 'Ошибка', 'Файл или папка с таким именем уже существует!')
            return

        if os.path.isfile(self.clipboard_path):
            shutil.copy2(self.clipboard_path, destination_path)
        elif os.path.isdir(self.clipboard_path):
            shutil.copytree(self.clipboard_path, destination_path)

        root_path = self.model.rootPath()
        self.model.setRootPath('')
        self.model.setRootPath(root_path)

        queue_message = f"PASTE_ITEM||{destination_path}"
        log_message = f"Файл {os.path.basename(self.clipboard_path)} успешно вставлен в {destination_folder}."
        log_path = "../logs/actions.log"

        self.update_processes(queue_message, log_message, log_path)

    def open_terminal(self):
        self.terminal = TerminalWindow()
        self.terminal.show()

        log_message = "Терминал успешно открыт."
        self.log_widget.append(log_message)

    def open_system_terminal(self):
        subprocess.Popen(['gnome-terminal'])

        log_message = "Системный терминал успешно открыт."
        self.log_widget.append(log_message)

    def open_system_browser(self):
        subprocess.Popen(['xdg-open', 'https://www.google.com/'])

        log_message = "Браузер успешно открыт."
        self.log_widget.append(log_message)

    def open_system_monitor(self):
        subprocess.Popen(['gnome-system-monitor'])

        log_message = "Системный монитор успешно открыт."
        self.log_widget.append(log_message)

    def open_system_calculator(self):
        subprocess.Popen(['gnome-calculator'])

        log_message = "Калькулятор успешно открыт."
        self.log_widget.append(log_message)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if self.is_system_folder(url.toLocalFile()):
                    event.ignore()
                    return
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if self.is_system_folder(url.toLocalFile()):
                    event.ignore()
                    return
            event.acceptProposedAction()

    def dropEvent(self, event):
        destination_index = self.tree.indexAt(event.pos())
        destination_folder = self.model.filePath(destination_index)

        if not os.path.exists(destination_folder):
            destination_folder = self.get_destination_folder(event.pos())

        for url in event.mimeData().urls():
            file_path = str(url.toLocalFile())
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(destination_folder, file_name)

            if os.path.commonpath([file_path, destination_path]) == os.path.commonpath([file_path]):
                continue

            if os.path.exists(file_path) and os.path.exists(destination_path):
                if not os.path.samefile(file_path, destination_path):
                    if os.path.isdir(file_path):
                        shutil.move(file_path, destination_path)
                        self.model.setRootPath('')
                        self.model.setRootPath(destination_folder)
                    elif os.path.isfile(file_path):
                        shutil.move(file_path, destination_path)
                        self.model.setRootPath('')
                        self.model.setRootPath(destination_folder)
            elif os.path.exists(file_path) and not os.path.exists(destination_path):
                if os.path.isdir(file_path):
                    shutil.move(file_path, destination_path)
                    self.model.setRootPath('')
                    self.model.setRootPath(destination_folder)
                elif os.path.isfile(file_path):
                    shutil.move(file_path, destination_path)
                    self.model.setRootPath('')
                    self.model.setRootPath(destination_folder)

    def is_system_folder(self, folder_path):
        system_folders = ["System", "Корзина"]
        folder_name = os.path.basename(folder_path)
        return folder_name in system_folders

    def get_destination_folder(self, position):
        index = self.tree.indexAt(position)
        if index.isValid():
            file_path = self.model.filePath(index)
            if os.path.isdir(file_path):
                return file_path
            else:
                return os.path.dirname(file_path)
        else:
            return self.model.rootPath()

    def show_about_info(self):
        QMessageBox.information(self, 'О программе',
                                'Операционные системы и оболочки: Linux\n'
                                'ЯП и фреймворк(-и): Python & PyQt5\n'
                                'ФИО и группа: Митрофанов Иван Алексеевич, ПрИ-23')

        queue_message = "ABOUT_INFO"
        log_message = f"Вкладка 'О программе' успешно открыта."
        log_path = "../logs/actions.log"

        self.update_processes(queue_message, log_message, log_path)

    def show_shortcuts(self):
        QMessageBox.information(self, 'Горячие клавиши',
                                'CTRL + C: Копирование объекта (файл, папка)\n'
                                'CTRL + V: Вставка объекта (файл, папка)\n'
                                'CTRL + Delete: Удаление объекта безвозратно (файл, папка)\n'
                                'CTRL + N: Создание файла в выбранной папке\n'
                                'CTRL + SHIFT + ALT + T: Открытие терминала\n'
                                'CTRL + R: Переименование объекта (файл, папка)\n'
                                'CTRL + I: Восстановить объекта (файл, папка)\n')

        queue_message = "SHORTCUTS"
        log_message = f"Вкладка 'Горячие клавиши' успешно открыта."
        log_path = "../logs/actions.log"

        self.update_processes(queue_message, log_message, log_path)

    def open_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        if os.path.isfile(file_path):
            try:
                os.startfile(file_path)  # для Windows
            except AttributeError:
                import subprocess
                subprocess.run(['xdg-open', file_path])  # для Linux

                queue_message = f"OPEN_ITEM|{file_path}"
                log_message = f"Файл {file_path} успешно открыт."
                log_path = "../logs/actions.log"

                self.update_processes(queue_message, log_message, log_path)
        else:
            QMessageBox.warning(self, 'Ошибка', 'Это не файл!')

    def show_context_menu(self, pos):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        self.contextMenu.clear()

        if file_path.endswith('/Корзина'):
            clear_trash_action = QAction('Очистить корзину', self)
            clear_trash_action.triggered.connect(self.clear_trash)

            self.contextMenu.addAction(clear_trash_action)
        else:
            if file_path.startswith(f'{DEFAULT_DIR_CATALOG}/Корзина'):
                restore_action = QAction('Восстановить (CTRL + I)', self)
                restore_action.triggered.connect(self.restore_item)

                self.contextMenu.addAction(restore_action)
            elif '/System' in file_path:
                create_folder_action = QAction('Создать папку (CTRL + SHIFT + N)', self)
                create_folder_action.triggered.connect(self.create_folder_item)
                create_file_action = QAction('Создать файл CTRL + N', self)
                create_file_action.triggered.connect(self.create_file_item)

                self.contextMenu.addAction(create_folder_action)
                self.contextMenu.addAction(create_file_action)
            else:
                if os.path.isfile(file_path):
                    open_action = QAction('Открыть', self)
                    open_action.triggered.connect(self.open_item)
                    delete_action = QAction('Удалить DELETE', self)
                    delete_action.triggered.connect(self.delete_item)
                    delete_immediately_action = QAction('Удалить сразу CTRL + DELETE', self)
                    delete_immediately_action.triggered.connect(self.delete_immediately_item)
                    rename_action = QAction('Переименовать CTRL + R', self)
                    rename_action.triggered.connect(self.rename_item)

                    self.contextMenu.addAction(open_action)
                    self.contextMenu.addAction(delete_action)
                    self.contextMenu.addAction(delete_immediately_action)
                    self.contextMenu.addAction(rename_action)
                else:
                    create_folder_action = QAction('Создать папку', self)
                    create_folder_action.triggered.connect(self.create_folder_item)
                    create_file_action = QAction('Создать файл CTRL + N', self)
                    create_file_action.triggered.connect(self.create_file_item)
                    rename_action = QAction('Переименовать CTRL + R', self)
                    rename_action.triggered.connect(self.rename_item)
                    delete_action = QAction('Удалить DELETE', self)
                    delete_action.triggered.connect(self.delete_item)
                    delete_immediately_action = QAction('Удалить сразу CTRL + DELETE', self)
                    delete_immediately_action.triggered.connect(self.delete_immediately_item)

                    self.contextMenu.addAction(create_folder_action)
                    self.contextMenu.addAction(create_file_action)
                    self.contextMenu.addAction(rename_action)
                    self.contextMenu.addAction(delete_action)
                    self.contextMenu.addAction(delete_immediately_action)

        message = f"CONTEXT_MENU|{file_path}"
        send_message(message)

        self.contextMenu.exec_(self.tree.mapToGlobal(pos))

    def create_root_folder(self):
        new_folder_name, ok = QInputDialog.getText(self, "Создание папки в корневой директории", "Введите имя папки:")
        if ok and new_folder_name:
            root_path = self.model.rootPath()
            new_folder_path = os.path.join(root_path, new_folder_name)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                self.model.setRootPath('')
                self.model.setRootPath(root_path)

                queue_message = "CREATE_ROOT_FOLDER"
                log_message = f"Папка {new_folder_name} успешно создана в корневой директории."
                log_path = "files.log"

                self.update_processes(queue_message, log_message, log_path)

    def create_root_file(self):
        new_file_name, ok = QInputDialog.getText(self, "Создание файла в корневой директории", "Введите имя файла:")
        if ok and new_file_name:
            if '.' not in new_file_name:
                new_file_name += '.txt'

            root_path = self.model.rootPath()
            new_file_path = os.path.join(root_path, new_file_name)
            open(new_file_path, 'a').close()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = "CREATE_ROOT_FILE"
            log_message = f"Файл {new_file_name} успешно создан в корневой директории."
            log_path = "files.log"

            self.update_processes(queue_message, log_message, log_path)

    def create_folder_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        new_folder_name, ok = QInputDialog.getText(self, "Создание папки", "Введите имя папки:")
        if ok and new_folder_name:
            full_folder_path = os.path.join(file_path, new_folder_name)

            if os.path.exists(full_folder_path):
                QMessageBox.warning(self, 'Ошибка', f'Папка с именем {new_folder_name} уже существует!')
                return

            os.makedirs(full_folder_path)
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = f"CREATE_FOLDER_ITEM|{file_path}"
            log_message = f"Папка {new_folder_name} успешно создана в {file_path}."
            log_path = "files.log"

            self.update_processes(queue_message, log_message, log_path)

    def create_file_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        new_file_name, ok = QInputDialog.getText(self, "Создание файла", "Введите имя файла:")
        if ok and new_file_name:
            if '.' not in new_file_name:
                new_file_name += '.txt'

            full_file_path = os.path.join(file_path, new_file_name)

            if os.path.exists(full_file_path):
                QMessageBox.warning(self, 'Ошибка', f'Файл или папка с именем {new_file_name} уже существует!')
                return

            open(full_file_path, 'a').close()
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = f"CREATE_FILE_ITEM|{file_path}"
            log_message = f"Файл {new_file_name} успешно создан в {file_path}."
            log_path = "files.log"

            self.update_processes(queue_message, log_message, log_path)

    def rename_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        if file_path.endswith('/System') or file_path.endswith('/Корзина'):
            QMessageBox.warning(self, 'Ошибка', 'Эту папку нельзя переименовать!')
            return

        new_name, ok = QInputDialog.getText(self, "Переименование", "Введите новое имя:")
        if ok and new_name:
            os.rename(file_path, os.path.join(os.path.dirname(file_path), new_name))
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = f"RENAME_ITEM|{file_path}"
            log_message = f"Объект успешно переименован в {new_name}."
            log_path = "files.log"

            self.update_processes(queue_message, log_message, log_path)

    def protect_source(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        if '/System' in file_path or file_path.endswith('/Корзина'):
            QMessageBox.warning(self, 'Ошибка', 'Эту папку нельзя удалить!')
            return

        return file_path

    def delete_item(self):
        index = self.tree.currentIndex()
        file_path = self.protect_source()

        trash_path = os.path.join(DEFAULT_DIR_CATALOG, 'Корзина')
        trash_file_path = os.path.join(trash_path, os.path.basename(file_path))

        self.original_paths[trash_file_path] = file_path

        os.rename(file_path, trash_file_path)

        queue_message = f"DELETE_ITEM|{file_path}"
        log_message = f"Файл или папка {os.path.basename(file_path)} успешно удалены."
        log_path = "delete.log"

        self.update_processes(queue_message, log_message, log_path)

    def delete_immediately_item(self):
        index = self.tree.currentIndex()
        file_path = self.protect_source()

        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)

        root_path = self.model.rootPath()
        self.model.setRootPath('')
        self.model.setRootPath(root_path)

        queue_message = f"DELETE_IMMEDIATELY_ITEM|{file_path}"
        log_message = f"Файл или папка {os.path.basename(file_path)} успешно удалены навсегда."
        log_path = "delete.log"

        self.update_processes(queue_message, log_message, log_path)

    def restore_item(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)

        original_path = self.original_paths.get(file_path, None)
        if not original_path:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось определить исходный путь файла!')
            return

        new_name, ok = QInputDialog.getText(self, "Восстановление",
                                            "Введите новое имя (или оставьте пустым для оригинального имени):")
        if ok:
            if not new_name:
                new_name = os.path.basename(original_path)
            new_file_path = os.path.join(original_path, new_name)

            if not os.path.exists(os.path.dirname(new_file_path)):
                os.makedirs(os.path.dirname(new_file_path))

            os.rename(file_path, new_file_path)
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = f"RESTORE_ITEM|{file_path}"
            log_message = f"Объект успешно восстановлен в {new_file_path}."
            log_path = "trash.log"

            self.update_processes(queue_message, log_message, log_path)

    def clear_trash(self):
        reply = QMessageBox.question(self, 'Очистить корзину',
                                     'Уверены ли вы, что хотите очистить корзину?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            trash_path = os.path.join(DEFAULT_DIR_CATALOG, 'Корзина')
            for filename in os.listdir(trash_path):
                file_path = os.path.join(trash_path, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)

            queue_message = "CLEAR_TRASH"
            log_message = "Корзина успешно очищена."
            log_path = "trash.log"

            self.update_processes(queue_message, log_message, log_path)
        else:
            return

    def search_item(self):
        search_text = self.searchInput.text().strip()
        if not search_text:
            root_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(root_path)
            return


        matches = self.find_items(search_text, Qt.MatchContains | Qt.MatchRecursive, 0)

        if matches:
            first_match = matches[0]
            self.tree.setCurrentIndex(first_match)
            self.tree.scrollTo(first_match)

            queue_message = f"SEARCH_ITEM|{search_text}"
            log_message = f"Поиск завершен. Найдено {len(matches)} совпадений."
            log_path = "trash.log"

            self.update_processes(queue_message, log_message, log_path)
        else:
            QMessageBox.information(self, 'Поиск', f'Файл или папка с именем "{search_text}" не найдены.')

    def find_items(self, text, _flags, _column):
        matches = []
        stack = [self.model.index(0, 0, QModelIndex())]

        while stack:
            index = stack.pop()
            if index.isValid():
                text_data = self.model.data(index, Qt.DisplayRole)
                if text_data and text in text_data:
                    matches.append(index)

                if self.model.hasChildren(index):
                    for row in range(self.model.rowCount(index)):
                        stack.append(self.model.index(row, 0, index))

        queue_message = f"FIND_ITEMS|{matches}"
        log_message = f"Поиск завершен. Найдено {len(matches)} совпадений."
        log_path = "trash.log"

        self.update_processes(queue_message, log_message, log_path)
        return matches


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SuperApp()
    window.show()
    sys.exit(app.exec_())
