from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer
import psutil
import subprocess


class TasksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Все задачи')
        self.setGeometry(200, 200, 600, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.users_info_label = QLabel("Информация о пользователях ОС:")
        self.layout.addWidget(self.users_info_label)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)  # Установка количества столбцов
        headers = ["USER", "TTY", "FROM", "LOGIN@", "IDLE", "JCPU", "PCPU", "WHAT"]
        self.users_table.setHorizontalHeaderLabels(headers)
        self.layout.addWidget(self.users_table)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tasks)
        self.timer.start(5000)  # 5000 milliseconds = 5 seconds

        self.update_tasks()  # Initial update

    def update_tasks(self):
        __all = list(psutil.process_iter())
        __user = [p for p in __all if p.username() != 'root']
        all_processes = len(__all)
        user_processes = len(__user)
        users_info = subprocess.check_output(["w"]).decode("utf-8")

        self.users_table.setRowCount(0)  # Clear previous data

        rows = users_info.strip().split('\n')
        self.users_table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            items = row.split()
            for j, item in enumerate(items):
                self.users_table.setItem(i, j, QTableWidgetItem(item))

        # self.users_info_label.setText("Информация о пользователях ОС:\n" + users_info)
        self.setWindowTitle(f'Все задачи ({user_processes}/{all_processes})')

