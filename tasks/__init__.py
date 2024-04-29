from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel


class TasksDialog(QDialog):
    def __init__(self, tasks, users_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Все задачи')
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        users_info_label = QLabel("Информация о пользователях ОС:")
        layout.addWidget(users_info_label)

        users_table = QTableWidget()
        users_table.setColumnCount(8)  # Установка количества столбцов
        headers = ["USER", "TTY", "FROM", "LOGIN@", "IDLE", "JCPU", "PCPU", "WHAT"]
        users_table.setHorizontalHeaderLabels(headers)

        rows = users_info.strip().split('\n')  # Разделение строк
        users_table.setRowCount(len(rows))  # Установка количества строк

        for i, row in enumerate(rows):
            items = row.split()  # Разделение данных в строке
            for j, item in enumerate(items):
                users_table.setItem(i, j, QTableWidgetItem(item))

        layout.addWidget(users_table)

        for task, data in tasks.items():
            label_task = QLabel(task)
            layout.addWidget(label_task)
            label_data = QLabel(data)
            layout.addWidget(label_data)

        self.setLayout(layout)
