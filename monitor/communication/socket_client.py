"""
Tools for communicating with the server with sockets

@author: Teddy Tortorici
"""

import socket
from monitor import get


def send(msg: str, host: str = "localhost", port: int = 62538) -> str:
    if msg:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect to server
            s.connect((host, port))

            # send message to server
            s.send(msg.encode())

            # get response from the server
            msg_back = s.recv(1024)
        # print(msg_back)
        return msg_back.decode()
    else:
        return "did not send anything"


def shutdown_command(host, port):
    send("shutdown")


class Device:
    """This class is meant to be inherited by classes dedicated to specific devices"""

    def __init__(self, dev_id):
        self.dev_id = dev_id
        self.host = "localhost"
        self.port = get.port()

    def query(self, msg: str) -> str:
        return self.send(f"{self.dev_id}::Q::{msg}")

    def write(self, msg: str) -> str:
        self.send(f"{self.dev_id}::W::{msg}")
        return "empty"

    def read(self) -> str:
        return self.send(f"{self.dev_id}::R")

    def raw(self, command) -> None:
        self.send(f"{self.dev_id}::{command}")

    def get_id(self) -> str:
        return self.query('*IDN?')

    def reset(self) -> str:
        self.write('*RST')
        return "reset"

    def send(self, msg: str) -> str:
        return send(msg, self.host, self.port)


if __name__ == "__main__":
    response = send('test')
    print(response)
