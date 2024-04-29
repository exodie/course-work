import os
import subprocess

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QShortcut


class TerminalWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.runButton = None
        self.commandInput = None
        self.terminalOutput = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Терминал')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.terminalOutput = QTextEdit()
        self.terminalOutput.setReadOnly(True)
        layout.addWidget(self.terminalOutput)

        send_message = QShortcut(QKeySequence("Ctrl+Enter"), self)
        send_message.activated.connect(self.execute_command)

        self.commandInput = QLineEdit()
        self.commandInput.setPlaceholderText("Введите команду")
        layout.addWidget(self.commandInput)

        self.runButton = QPushButton("Выполнить")
        layout.addWidget(self.runButton)
        self.runButton.clicked.connect(self.execute_command)

        self.setLayout(layout)

    def execute_command(self):
        command = self.commandInput.text().strip()

        allowed_commands = [
            'help', 'clear', 'ps', 'top', 'kill',
            'lsof', 'fdisk', 'mount', 'unmount', 'dmesg',
            'lsusb', 'lspci', 'lsblk', 'iwconfig', 'ifup', 'ifdown'
        ]

        if command.split()[0] not in allowed_commands:
            self.terminalOutput.append("Недопустимая команда!")
            return

        if command == 'help':
            help_text = """
            Доступные команды:
            - help: Справочная информация о доступных командах
            - clear: Очистка экрана
            - ps: Просмотр запущенных процессов
            - top: Просмотр текущих процессов
            - kill: Завершение процесса
            - lsof: Список открытых файлов
            - fdisk: Управление разделами диска
            - mount: Монтирование файловых систем
            - unmount: Демонтирование файловых систем
            - dmesg: Просмотр системных сообщений
            - lsusb: Просмотр USB устройств
            - lspci: Просмотр PCI устройств
            - lsblk: Просмотр блочных устройств
            - iwconfig: Конфигурация беспроводных сетей
            - ifup: Включение сетевого интерфейса
            - ifdown: Выключение сетевого интерфейса
            """

            self.terminalOutput.append(help_text)
            self.commandInput.clear()
            return

        if command == "clear":
            self.terminalOutput.clear()
            self.commandInput.clear()
            return

        try:
            env = os.environ.copy()
            env['TERM'] = 'xterm'
            result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))

        self.commandInput.clear()
