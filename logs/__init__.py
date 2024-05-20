import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog

from System.shared import DEFAULT_DIR_CATALOG


class LogFileDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Выберите лог-файл')
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        self.path_label = QLabel('Путь к лог-файлу:')
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText('/logs/name_file.log')
        self.browse_button = QPushButton('Обзор...')
        self.browse_button.clicked.connect(self.browse_file)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton('Отмена')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)
        layout.addWidget(self.browse_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите лог-файл', f'{DEFAULT_DIR_CATALOG}/logs/',
                                                   'Log files (*.log)')
        if file_path:
            self.path_input.setText(file_path)

    def get_file_path(self):
        return self.path_input.text()


def create_logs_with_msg(msg: str, file_name: str):
    log_file_path = os.path.join(f"{DEFAULT_DIR_CATALOG}/logs", file_name)

    with open(log_file_path, "a") as log_file:
        log_file.write(msg + "\n")
