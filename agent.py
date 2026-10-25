
import random
import threading
import time

from node import Node

AGENTS = ["Happy", "Sad", "Love"]

WORD_BANKS = {
    "Happy": [
        "sunshine", "smiling", "bright",
        "golden", "joyful", "dancing"
    ],
    "Sad": [
        "tears", "lonely", "broken",
        "silent", "weary", "sorrow"
    ],
    "Love": [
        "forever", "beloved", "heart",
        "rose", "passion", "tender"
    ]
}


class Agent(Node):
    def __init__(self, name):
        super().__init__(name)
        self.send_threads = []
        self.send_threads_lock = threading.Lock()

    def on_message(self, message):
        if message["type"] not in ("REQUEST", "VERSE"):
            return

        remaining = message["remaining"]

        if remaining <= 0:
            return

        poem_id = message["poem_id"]

        # A REQUEST starts a new chain.
        # A VERSE continues an existing chain.
        if message["type"] == "REQUEST":
            previous_words = 0
            received_clock = None
        else:
            previous_words = message["word_count"]
            received_clock = message["clock"]

        word_count = previous_words + 1

        # Create one verse event.
        with self.lock:
            if received_clock is not None:
                self.vc.merge(received_clock)

            self.vc.increment()
            clock = self.vc.get_clock()

            words = random.choices(
                WORD_BANKS[self.name],
                k=word_count
            )
            verse = poem_id + " " + " ".join(words)

        print(f"{self.name} generated: {verse} {clock}")

        verse_message = {
            "type": "VERSE",
            "sender": self.name,
            "poem_id": poem_id,
            "verse": verse,
            "word_count": word_count,
            "remaining": remaining - 1,
            "clock": clock
        }

        # Select a different agent.
        other_agents = [
            name for name in AGENTS
            if name != self.name
        ]
        next_agent = random.choice(other_agents)

        # Two independently delayed sends.
        self.delayed_send("Poet", verse_message)

        # if remaining > 1:
        #     self.delayed_send(next_agent, verse_message)
        self.delayed_send(next_agent, verse_message)

    
    def delayed_send(self, target, message):
        def worker():
            delay = random.uniform(0.2, 0.8)
            time.sleep(delay)

            self.send_message(target, message)

            print(
                f"{self.name} -> {target} "
                f"after {delay:.2f}s "
                f"clock={message['clock']}"
            )

        thread = threading.Thread(
            target=worker
        )

        with self.send_threads_lock:
            self.send_threads.append(thread)

        thread.start()

    def wait_for_sends(self):
        with self.send_threads_lock:
            threads = self.send_threads[:]

        for thread in threads:
            thread.join()
