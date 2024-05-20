import threading
import time

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QWidget, QDialog
from sysv_ipc import MessageQueue


class DataWindow(QWidget):
    def __init__(self, key, window_id):
        super().__init__()

        self.queue = MessageQueue(key)
        self.window_id = window_id

        self.setWindowTitle(f"Tasks {window_id}")
        self.setGeometry(150 * window_id, 150 * window_id, 300, 200)

        self.label = QLabel("", self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Start the update thread
        self.update_thread = threading.Thread(target=self.update_label)
        self.update_thread.daemon = True
        self.update_thread.start()

    def update_label(self):
        while True:
            try:
                message, _ = self.queue.receive(block=False)
                self.label.setText(message.decode())
            except Exception:
                pass
            time.sleep(1)


class Receiver(QObject):
    data_received = pyqtSignal(dict)

    def __init__(self, key):
        super().__init__()
        self.queue = MessageQueue(key)

    def run(self):
        while True:
            try:
                message, _ = self.queue.receive(block=False)
                user_info_str = message.decode()
                rows = user_info_str.split('\n')
                data = {"rows": rows}
                self.data_received.emit(data)
            except Exception:
                pass
            time.sleep(1)


class UserTableWindow(QDialog):
    def __init__(self, key, window_id):
        super().__init__()

        self.setWindowTitle(f"User Info Window {window_id}")
        self.setGeometry(200, 200, 600, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.users_info_label = QLabel("Информация о пользователях ОС:")
        self.layout.addWidget(self.users_info_label)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        headers = ["USER", "TTY", "FROM", "LOGIN@"]
        self.users_table.setHorizontalHeaderLabels(headers)
        self.layout.addWidget(self.users_table)

        self.receiver = Receiver(key)
        self.thread = QThread()
        self.receiver.moveToThread(self.thread)
        self.thread.started.connect(self.receiver.run)
        self.receiver.data_received.connect(self.update_table)

        self.thread.start()

    def update_table(self, data):
        rows = data["rows"]

        self.users_table.setRowCount(0)
        self.users_table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            items = row.split()
            for j, item in enumerate(items):
                self.users_table.setItem(i, j, QTableWidgetItem(item))