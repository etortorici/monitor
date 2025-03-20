import numpy as np
import time
from monitor.communication.gpib import Fake


class Lakeshore(Fake):
    def __init__(self):
        super(Lakeshore, self).__init__()
        self.start_time = time.time()

    def query(self, msg: str) -> str:
        time.sleep(0.5)
        if msg == "KRDG? A" or msg == "KRDG? B":
            return f"{300 * np.exp(-self.start_time / 4096.) + np.random.random():.2f}"
        elif msg == "HTR?":
            return "99"
        elif msg == "RANGE?":
            return "1"
        elif msg == "PID? 1" or msg == "PID? 2":
            return "80., 15., 10."
        elif msg == "RAMP? 1" or msg == "RAMP? 2":
            return "1, 6."
        elif msg == "RAMPST?":
            return "1"
        elif msg == "SETP? 1" or msg == "SETP? 2":
            return "30."
        else:
            return "nothing"


class Bridge(Fake):
    def __init__(self):
        super(Bridge, self).__init__()
        self.frequency = 100
        self.voltage = 1.5

    def write(self, msg: str):
        if msg[:2] == "FR":
            self.frequency = int(msg.lstrip("FR"))
        elif msg[0] == "V":
            self.voltage = float(msg.lstrip("V"))

    def query(self, msg: str) -> str:
        time.sleep(0.5)
        if msg == "SH AV":
            return "7"
        elif msg == "Q":
            return "F = {f} HZ C = {c:.5f} PF L = {d:.5f} V = {v} V".format(f=self.frequency,
                                                                            c=1 + 0.2 * np.random.random(),
                                                                            d=0.003 * np.random.random(),
                                                                            v=self.voltage)
        elif msg == "SH UN":
            return "DS"
        elif msg == "SH FR":
            return str(self.frequency)
