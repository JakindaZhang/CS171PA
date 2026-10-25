class VectorClock:
    def __init__(self, index):
        self.clock = [0, 0, 0]
        self.index = index

    def increment(self):
        self.clock[self.index] += 1

    def merge(self, received_clock):
        for i in range(3):
            self.clock[i] = max(
                self.clock[i],
                received_clock[i]
            )

    def get_clock(self):
        return self.clock.copy()
