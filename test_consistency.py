
import ast
import re
from collections import Counter
from pathlib import Path

OUTPUT = Path("outputs")
POEM = OUTPUT / "poem.txt"
POET_LOG = OUTPUT / "poet.log"

EXPECTED = {
    "FIRST": 3,
    "SECOND": 4,
    "THIRD": 5
}


def test_poem():
    lines = POEM.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 12, (
        f"Expected 12 verses, got {len(lines)}"
    )

    counts = Counter()
    delivered = [0, 0, 0]

    for line in lines:
        match = re.fullmatch(
            r"(.+?)\s+(\[[0-9,\s]+\])",
            line
        )
        assert match, f"Invalid line: {line}"

        verse = match.group(1)
        clock = ast.literal_eval(match.group(2))

        assert len(clock) == 3
        assert all(
            isinstance(x, int) and x >= 0
            for x in clock
        )

        words = verse.split()
        prefix = words[0]

        assert prefix in EXPECTED
        counts[prefix] += 1

        assert len(words) - 1 == counts[prefix], (
            f"Wrong word count: {verse}"
        )

        # Infer the sender from the one component
        # that is exactly one step ahead.
        candidates = [
            i for i in range(3)
            if clock[i] == delivered[i] + 1
            and all(
                clock[j] <= delivered[j]
                for j in range(3) if j != i
            )
        ]

        assert len(candidates) == 1, (
            f"Causal delivery violation: {clock}, "
            f"delivered={delivered}"
        )

        delivered = [
            max(delivered[i], clock[i])
            for i in range(3)
        ]

    assert dict(counts) == EXPECTED, (
        f"Wrong verse counts: {counts}"
    )

    print("PASS: Poem structure and causal order")
    print("Final delivered clock:", delivered)


def test_logs():
    lines = POET_LOG.read_text(
        encoding="utf-8"
    ).splitlines()

    counts = Counter()

    for line in lines:
        match = re.match(
            r"#\d+\s+(SEND|RECV|OUTPUT)\b",
            line
        )
        if match:
            counts[match.group(1)] += 1

    assert counts["SEND"] == 3
    assert counts["RECV"] == 12
    assert counts["OUTPUT"] == 12

    print("PASS: Poet log event counts")


if __name__ == "__main__":
    test_poem()
    test_logs()
    print("\nALL TESTS PASSED")
