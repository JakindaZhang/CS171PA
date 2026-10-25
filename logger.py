
import threading
from pathlib import Path


class MessageLogger:
    def __init__(self, name):
        Path("outputs").mkdir(exist_ok=True)

        self.name = name
        self.sequence = 0
        self.lock = threading.Lock()

        self.file = open(
            f"outputs/{name.lower()}.log",
            "w",
            encoding="utf-8"
        )

    def log(self, action, peer, message,
            message_clock, local_clock):
        with self.lock:
            self.sequence += 1

            line = (
                f"#{self.sequence} "
                f"{action:<6} "
                f"{peer:<12} "
                f"msg_clock={message_clock} "
                f"local_clock={local_clock} "
                f"message={message}"
            )

            self.file.write(line + "\n")
            self.file.flush()

    def close(self):
        with self.lock:
            self.file.close()
