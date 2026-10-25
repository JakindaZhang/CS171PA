
import shutil
import subprocess
import sys
import time
from pathlib import Path

from test_consistency import test_poem, test_logs

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
ARCHIVE = ROOT / "stress_results"

ROUNDS = 20
TIMEOUT = 30

NODES = ["Happy", "Sad", "Love", "Poet"]

def count_events(filename, action):
    path = OUTPUT / filename
    if not path.exists():
        return 0

    return sum(
        1 for line in path.read_text().splitlines()
        if line.split()[1:2] == [action]
    )


def complete():
    poem = OUTPUT / "poem.txt"
    if not poem.exists():
        return False

    if len(poem.read_text().splitlines()) != 12:
        return False

    if (
        count_events("poet.log", "SEND") != 3
        or count_events("poet.log", "RECV") != 12
        or count_events("poet.log", "OUTPUT") != 12
    ):
        return False

    agent_sends = sum(
        count_events(f"{name.lower()}.log", "SEND")
        for name in ["Happy", "Sad", "Love"]
    )

    agent_receives = sum(
        count_events(f"{name.lower()}.log", "RECV")
        for name in ["Happy", "Sad", "Love"]
    )

    return agent_sends == 24 and agent_receives == 15


def run_round(number):
    processes = []
    round_dir = ARCHIVE / f"round_{number:02d}"
    round_dir.mkdir(parents=True, exist_ok=True)

    # Remove previous output before starting.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    try:
        for name in NODES:
            log_file = open(
                round_dir / f"{name.lower()}_console.txt",
                "w"
            )

            try:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "run_node.py",
                        name
                    ],
                    cwd=ROOT,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
            finally:
                log_file.close()

            processes.append(process)

            # Start agents first, Poet last.
            time.sleep(0.25)

        start = time.monotonic()

        while time.monotonic() - start < TIMEOUT:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        "A node exited unexpectedly"
                    )

            if complete():
                test_poem()
                test_logs()
                return True

            time.sleep(0.1)

        raise TimeoutError("Incomplete run")

    except Exception as error:
        print(f"Round {number} FAILED: {error}")
        return False

    finally:
        # Stop all processes.
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        # Preserve this round's output.
        for path in OUTPUT.glob("*"):
            if path.is_file():
                shutil.copy2(path, round_dir / path.name)


def main():
    ARCHIVE.mkdir(exist_ok=True)

    passed = 0

    for i in range(1, ROUNDS + 1):
        print(f"\n===== ROUND {i}/{ROUNDS} =====")

        if run_round(i):
            passed += 1
            print(f"ROUND {i}: PASS")
        else:
            print(f"ROUND {i}: FAIL")

    print("\n===== FINAL RESULTS =====")
    print(f"Passed: {passed}/{ROUNDS}")
    print(f"Failed: {ROUNDS - passed}/{ROUNDS}")


if __name__ == "__main__":
    main()