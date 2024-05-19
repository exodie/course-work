import datetime
import os
import subprocess

import psutil
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

        getattr(self, command.split()[0])()

    def help(self):
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

    def clear(self):
        self.terminalOutput.clear()
        self.commandInput.clear()

    def ps(self):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    processes.append(
                        f"{proc_info['pid']:>5} {proc_info['username']:<15} {proc_info['cpu_percent']:>5}% {proc_info['memory_info'].rss / 1024 ** 2:>8.2f} MB {proc_info['name']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            output = "\n".join(processes)
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def top(self):
        try:
            output = []

            load_avg = psutil.getloadavg()
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())

            output.append(f"System Uptime: {uptime}")
            output.append(f"Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
            output.append(f"Total Memory: {mem.total / 1024 ** 2:.2f} MB")
            output.append(f"Used Memory: {mem.used / 1024 ** 2:.2f} MB ({mem.percent}%)")
            output.append(f"Free Memory: {mem.free / 1024 ** 2:.2f} MB")
            output.append(f"Total Swap: {swap.total / 1024 ** 2:.2f} MB")
            output.append(f"Used Swap: {swap.used / 1024 ** 2:.2f} MB ({swap.percent}%)")
            output.append(f"Free Swap: {swap.free / 1024 ** 2:.2f} MB")
            output.append("")

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    processes.append((proc_info['cpu_percent'], proc_info))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            processes.sort(key=lambda x: x[0], reverse=True)

            output.append(f"{'PID':>5} {'USER':<15} {'%CPU':>5} {'%MEM':>5} {'RSS (MB)':>10} COMMAND")
            for cpu_percent, proc_info in processes[:10]:
                rss = proc_info['memory_info'].rss / 1024 ** 2
                output.append(
                    f"{proc_info['pid']:>5} {proc_info['username']:<15} {cpu_percent:>5.1f} {rss / mem.total * 100:>5.1f} {rss:>10.2f} {proc_info['name']}")

            self.terminalOutput.append("\n".join(output))
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def kill(self):
        try:
            process_id = self.commandInput.text().split()[1] if len(self.commandInput.text().split()) > 1 else ''
            if process_id.isdigit():
                result = subprocess.run(['kill', process_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = result.stdout.decode() if result.stdout else result.stderr.decode()
                self.terminalOutput.append(output)
            else:
                self.terminalOutput.append("Некорректный идентификатор процесса")
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def lsof(self):
        try:
            output = []

            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    files = proc.open_files()
                    if files:
                        for file in files:
                            output.append(
                                f"{proc.info['pid']:>5} {proc.info['username']:<15} {proc.info['name']:<25} {file.path}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if output:
                self.terminalOutput.append("\n".join(output))
            else:
                self.terminalOutput.append("Нет открытых файлов.")
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def fdisk(self):
        try:
            output = []

            partitions = psutil.disk_partitions()
            for partition in partitions:
                output.append(f"Device: {partition.device}")
                output.append(f"  Mountpoint: {partition.mountpoint}")
                output.append(f"  Filesystem type: {partition.fstype}")
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    output.append(f"  Total Size: {usage.total / 1024 ** 3:.2f} GB")
                    output.append(f"  Used: {usage.used / 1024 ** 3:.2f} GB")
                    output.append(f"  Free: {usage.free / 1024 ** 3:.2f} GB")
                    output.append(f"  Usage: {usage.percent}%")
                except PermissionError:
                    output.append("  Permission Denied to access usage information")
                output.append("")

            self.terminalOutput.append("\n".join(output))
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def mount(self):
        try:
            output = []

            partitions = psutil.disk_partitions()
            for partition in partitions:
                output.append(
                    f"{partition.device} on {partition.mountpoint} type {partition.fstype} ({partition.opts})")

            if output:
                self.terminalOutput.append("\n".join(output))
            else:
                self.terminalOutput.append("Нет смонтированных файловых систем.")
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def unmount(self):
        try:
            command_text = self.commandInput.text().split()
            mount_point = command_text[1] if len(command_text) > 1 else ''

            if mount_point:
                try:
                    result = subprocess.run(['umount', mount_point], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output = result.stdout.decode() if result.stdout else result.stderr.decode()
                    self.terminalOutput.append(output)
                except Exception as e:
                    self.terminalOutput.append(f"Ошибка при размонтировании {mount_point}: {str(e)}")
            else:
                self.terminalOutput.append("Некорректная точка монтирования")
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def dmesg(self):
        try:
            dmesg_output = os.popen('dmesg').read()
            if dmesg_output:
                self.terminalOutput.append(dmesg_output)
            else:
                self.terminalOutput.append("Не удалось получить сообщения ядра.")
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def lsusb(self):
        try:
            result = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def lspci(self):
        try:
            result = subprocess.run(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def lsblk(self):
        try:
            result = subprocess.run(['lsblk'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def iwconfig(self):
        try:
            result = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def ifup(self):
        interface = self.commandInput.text().split()[1] if len(self.commandInput.text().split()) > 1 else ''
        try:
            result = subprocess.run(['ifup', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()

    def ifdown(self):
        interface = self.commandInput.text().split()[1] if len(self.commandInput.text().split()) > 1 else ''
        try:
            result = subprocess.run(['ifdown', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode() if result.stdout else result.stderr.decode()
            self.terminalOutput.append(output)
        except Exception as e:
            self.terminalOutput.append(str(e))
        self.commandInput.clear()
