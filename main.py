
import threading
import time

from agent import Agent
from poet import Poet


poet = Poet(expected_verses=12)
happy = Agent("Happy")
sad = Agent("Sad")
love = Agent("Love")

nodes = [poet, happy, sad, love]
agents = [happy, sad, love]

for node in nodes:
    threading.Thread(
        target=node.start_server,
        daemon=True
    ).start()

time.sleep(0.5)

requests = [
    ("Happy", "FIRST", 3),
    ("Sad", "SECOND", 4),
    ("Love", "THIRD", 5)
]

request_threads = []

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
    request_threads.append(thread)

for thread in request_threads:
    thread.join()

completed = poet.finished.wait(timeout=20)

if completed:
    print("\nSUCCESS: All 12 verses delivered!")
else:
    print("\nTIMEOUT: Not all verses delivered.")
    print("Delivered:", poet.output_count)
    print("Buffered:", len(poet.buffer))

# Finish pending outgoing messages.
for agent in agents:
    agent.wait_for_sends()

# Allow final TCP receives to be processed.
time.sleep(0.5)

poet.close()

for node in nodes:
    node.close_logger()

print("\nOutput files saved in outputs/")
