"""
The script allows you to establish connections to instruments over GPIB

author: Teddy Tortorici
"""

import pyvisa
import numpy as np


class Device:
    def __init__(self, address: int, gpib_num: int = 0, termination: str = "\r\n"):
        """
        Establish connection with a device over GPIB at address 'address' for interface 'gpib_num'
        :param address: the devices address
        :param gpib_num: the interfaces number
        """
        self.address = address
        self.gpib_num = gpib_num
        self.rm = pyvisa.ResourceManager()
        self.dev = self.rm.open_resource(f"GPIB{gpib_num}::{address}::INSTR", read_termination=termination)
        # self.id = self.get_id()

    def read(self) -> str:
        """Reads from the device connected to"""
        try:
            return self.dev.read()
        except pyvisa.errors.VisaIOError:
            return "timed out"

    def write(self, msg: str):
        """Write to the device connected to"""
        try:
            self.dev.write(msg)
            return "sent"
        except pyvisa.errors.VisaIOError:
            return "timed out"

    def query(self, msg: str) -> str:
        """Write to the device and then read its response"""
        try:
            return self.dev.query(msg)
        except pyvisa.errors.VisaIOError:
            return "timed out"

    def query_ascii(self, msg: str, sep=',', converter='f') -> np.ndarray | str:
        """Return an array of values from ascii request for large requests. Converter 'f' is to store floats."""
        try:
            return np.array(self.dev.query_ascii_values(msg, separator=sep, converter=converter))
        except pyvisa.errors.VisaIOError:
            return "timed out"

    def get_id(self):
        return self.query("*IDN?")

    def __str__(self):
        return f"{self.id:s} at GPIB{self.gpib_num}::{self.address:d}"


class Fake:
    def __init__(self):
        self.address = 0
        self.gpib_num = 0
        self.rm = None
        self.dev = None

    @staticmethod
    def read() -> str:
        """Reads from the device connected to"""
        return "Read from fake GPIB interface"

    @staticmethod
    def write(msg: str):
        """Write to the device connected to"""
        pass

    @staticmethod
    def query(msg: str) -> str:
        """Write to the device and then read its response"""
        return f"You queried the fake GPIB interface with {msg}"

    @staticmethod
    def query_ascii(msg: str, sep=',', converter='f') -> np.ndarray:
        """Return an array of values from ascii request for large requests. Converter 'f' is to store floats."""
        return np.arange(10)

    @staticmethod
    def get_id():
        return "This is a fake GPIB interface device"


if __name__ == "__main__":
    ls = Device(13)
    print(ls)
    ah = Device(28, termination="\n")
    print(ah)
