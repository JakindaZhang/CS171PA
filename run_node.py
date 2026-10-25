
import sys
import time
import threading

from agent import Agent
from poet import Poet


def start_requests(poet):
    time.sleep(1)

    requests = [
        ("Happy", "FIRST", 3),
        ("Sad", "SECOND", 4),
        ("Love", "THIRD", 5)
    ]

    threads = []

    for target, poem_id, count in requests:
        thread = threading.Thread(
            target=poet.send_message,
            args=(
                target,
                {
                    "type": "REQUEST",
                    "sender": "Poet",
                    "poem_id": poem_id,
                    "remaining": count,
                    "clock": [0, 0, 0]
                }
            )
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python3 run_node.py "
            "[Poet|Happy|Sad|Love]"
        )
        sys.exit(1)

    name = sys.argv[1]

    if name == "Poet":
        node = Poet(expected_verses=12)

        threading.Thread(
            target=start_requests,
            args=(node,),
            daemon=True
        ).start()

    elif name in ("Happy", "Sad", "Love"):
        node = Agent(name)

    else:
        print("Unknown node:", name)
        sys.exit(1)

    print(f"Starting {name}...")
    node.start_server()


if __name__ == "__main__":
    main()
