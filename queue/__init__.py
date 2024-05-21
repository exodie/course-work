import logging

from sysv_ipc import IPC_CREAT, MessageQueue

msg_queue = MessageQueue(1234, IPC_CREAT, mode=0o666)

logging.basicConfig(filename='../logs/queue/message_queue.log', level=logging.INFO)


def send_message(message):
    msg_queue.send(message)
    logging.info(f"Sent message: {message}")


def receive_message():
    message, _ = msg_queue.receive()
    logging.info(f"Received message: {message}")
    return message
