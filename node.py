
import socket
import threading
import json

from vector_clock import VectorClock
from logger import MessageLogger

HOST = "127.0.0.1"

PORTS = {
    "Poet": 5000,
    "Happy": 5001,
    "Sad": 5002,
    "Love": 5003
}

AGENT_INDEX = {
    "Happy": 0,
    "Sad": 1,
    "Love": 2
}


class Node:
    def __init__(self, name):
        self.name = name
        self.port = PORTS[name]

        self.lock = threading.Lock()
        self.process_lock = threading.Lock()
        self.logger = MessageLogger(name)

        if name in AGENT_INDEX:
            self.vc = VectorClock(AGENT_INDEX[name])
        else:
            self.vc = None

    def current_clock(self):
        with self.lock:
            if self.vc is not None:
                return self.vc.get_clock()

            return self.delivered_clock.copy()

    def start_server(self):
        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind((HOST, self.port))
        server.listen()

        print(f"{self.name} listening on {self.port}")

        while True:
            conn, addr = server.accept()

            threading.Thread(
                target=self.handle_connection,
                args=(conn,),
                daemon=True
            ).start()

    def handle_connection(self, conn):
        with conn:
            with conn.makefile("r") as stream:
                for line in stream:
                    message = json.loads(line)

                    with self.process_lock:
                        self.logger.log(
                            "RECV",
                            f"<- {message['sender']}",
                            message,
                            message.get("clock", [0, 0, 0]),
                            self.current_clock()
                        )

                        self.on_message(message)

    def on_message(self, message):
        print(f"{self.name} received: {message}")

    def next_verse_clock(self, received_clock=None):
        if self.vc is None:
            raise ValueError("Poet cannot generate verses")

        with self.lock:
            if received_clock is not None:
                self.vc.merge(received_clock)

            self.vc.increment()
            return self.vc.get_clock()

    def send_message(self, target, message):
        with socket.create_connection(
            (HOST, PORTS[target])
        ) as sock:
            data = json.dumps(message) + "\n"
            sock.sendall(data.encode("utf-8"))

        self.logger.log(
            "SEND",
            f"-> {target}",
            message,
            message.get("clock", [0, 0, 0]),
            self.current_clock()
        )

    def close_logger(self):
        self.logger.close()
