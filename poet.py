
import threading
from pathlib import Path

from node import Node, AGENT_INDEX


class Poet(Node):
    def __init__(self, expected_verses):
        super().__init__("Poet")

        # Vector clock for delivered verses
        self.delivered_clock = [0, 0, 0]

        # Messages waiting for causal dependencies
        self.buffer = []

        # Number of verses expected
        self.expected_verses = expected_verses
        self.output_count = 0

        self.finished = threading.Event()

        # Create output directory and poem file
        Path("outputs").mkdir(exist_ok=True)

        self.poem_file = open(
            "outputs/poem.txt",
            "w",
            encoding="utf-8"
        )

    def can_deliver(self, message):
        timestamp = message["clock"]
        sender_index = AGENT_INDEX[message["sender"]]

        # Sender must be exactly one event ahead
        if timestamp[sender_index] != (
            self.delivered_clock[sender_index] + 1
        ):
            return False

        # Other causal dependencies must be delivered
        for i in range(3):
            if i != sender_index:
                if timestamp[i] > self.delivered_clock[i]:
                    return False

        return True

    
    def deliver(self, message):
        timestamp = message["clock"]

        # 1. Update delivered clock first
        for i in range(3):
            self.delivered_clock[i] = max(
                self.delivered_clock[i],
                timestamp[i]
            )

        # 2. Write verse
        line = f"{message['verse']} {timestamp}"
        print("OUTPUT:", line)

        self.poem_file.write(line + "\n")
        self.poem_file.flush()

        # 3. Log updated clock
        self.logger.log(
            "OUTPUT",
            f"from {message['sender']}",
            message,
            timestamp,
            self.delivered_clock.copy()
        )

        # 4. Update completion counter
        self.output_count += 1

        if self.output_count == self.expected_verses:
            self.finished.set()

    def flush_buffer(self):
        while True:
            delivered_something = False

            for message in self.buffer[:]:
                if self.can_deliver(message):
                    self.buffer.remove(message)
                    self.deliver(message)
                    delivered_something = True
                    break

            if not delivered_something:
                break

    def on_message(self, message):
        if message["type"] != "VERSE":
            return

        with self.lock:
            print(
                "RECEIVED:",
                message["verse"],
                message["clock"]
            )

            if self.can_deliver(message):
                self.deliver(message)
                self.flush_buffer()
            else:
                self.buffer.append(message)
                print(
                    "BUFFERED:",
                    message["verse"],
                    message["clock"]
                )

    def close(self):
        with self.lock:
            self.poem_file.close()
