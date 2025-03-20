"""
Server functions that allow us to communicate over sockets to control devices

author: Teddy Tortorici
"""

import time
import socket
import monitor.get as get
import monitor.communication.gpib as gpib
import monitor.communication.fake_gpib as fake


class AH:
    units = "DS"            # for dissipation factor tan(delta)

    notation = "FLOAT"      # specifies the type of numeric notation to be used FLOATing, SCI, or ENG
    labeling = "OFF"        # enables labeling the values when set to ON
    ieee = "ON"             # enables IEEE-488.2 compatible punctuation when set to ON
    fld_width = "FIX"       # fixes field widths when set to FIXed. Else: VARiable

    formatting = (notation, labeling, ieee, fld_width)


class LS:
    loop = 1        # 1 or 2
    input = "A"     # channel A or B
    units = 1       # 1 for K, 2 for C, 3 for sensor units
    enabled = 1     # 1 to enable; 0 to disable
    powerup = 2     # 1 to enable; 0 to disable on powerup

    control_loop = (loop, input, units, enabled, powerup)


class GpibServer:

    shutdown_command = b"shutdown"

    """ADDRESSES"""
    addr_bridge = {"AH": 28, "HP": 5}
    addr_ls = {331: 13, 340: 12}

    def __init__(self, bridge_type: str = "AH", ls_model: int = 331, timeout: int = None):
        self.host_port = ("localhost", get.port())
        self.running = False
        self.writing_q_to_bridge = False
        print("Creating server.\n")

        """DEVICES"""
        if bridge_type == "FAKE" or bridge_type is None:
            self.bridge = fake.Bridge()
            print('"Connected" to FAKE bridge.\n')
        else:
            self.bridge = gpib.Device(GpibServer.addr_bridge[bridge_type], termination="\n")
            if timeout:
                self.bridge.dev.timeout = timeout
            print("Connected to bridge.")

            """STARTUP COMMANDS"""
            self.bridge.write("FORMAT {}, {}, {}, {}".format(*AH.formatting))
            print("Formatted: Notation: {}; Labeling: {}; IEEE-488.2: {}; Field Width: {}.".format(*AH.formatting))
            self.bridge.write("UNITS {}".format(AH.units))
            print("Set units to {}.".format(AH.units))
        if ls_model == "FAKE" or ls_model is None:
            self.ls = fake.Lakeshore()
            print('"Connected" to FAKE Lakeshore.\n')
        else:
            self.ls = gpib.Device(GpibServer.addr_ls[ls_model])
            print("\nConnected to LS{}".format(ls_model))

            """STARTUP COMMANDS"""
            self.ls.write("CSET {},{},{},{},{}".format(*LS.control_loop))
            unit_dict = ["", "K", "C", "sensor"]
            on_dict = ["off", "on", "on"]
            print("Control loop configured: Loop: {}; Channel: {}; Units: {}; Enabled: {}; Powerup: {}.\n".format(
                LS.control_loop,
                LS.input,
                unit_dict[LS.units],
                on_dict[LS.enabled],
                on_dict[LS.powerup]
            ))

    def handle(self, message_to_parse: str) -> str:
        """Parse a message of the format
        [Instrument ID]::[command]::[optional message]"""
        # print("\nHandling message:")
        msg_list = message_to_parse.split('::')
        dev_id = msg_list[0]
        command = msg_list[1]
        try:
            message = msg_list[2]
        except IndexError:
            message = ""

        if dev_id == "LS":
            if command[0] == "W":
                # print(f'Writing "{message}" to LS')
                self.ls.write(message)
                msgout = 'empty'
            elif command[0] == "Q":
                # print(f'Querying LS with "{message}"')
                msgout = self.ls.query(message)
            elif command[0] == "R":
                if dev_id in ["AH", "HP"]:
                    self.writing_q_to_bridge = False
                # print('Reading from LS')
                msgout = self.ls.read()
            else:
                msgout = "error"
        elif dev_id in ["AH", "HP"]:
            if command[0] == "W":
                if message == "Q":
                    self.writing_q_to_bridge = True
                # print(f'Writing "{message}" to {dev_id}')
                self.bridge.write(message)
                if self.writing_q_to_bridge:
                    self.bridge.write("Q")
                msgout = 'empty'
            elif command[0] == "Q":
                # print(f'Querying {dev_id} with "{message}"')
                msgout = self.bridge.query(message)
            elif command[0] == "R":
                if dev_id in ["AH", "HP"]:
                    self.writing_q_to_bridge = False
                # print(f'Reading from {dev_id}')
                msgout = self.bridge.read()
            elif command[0] == "F":
                self.bridge.write("FORMAT {}, {}, {}, {}".format(*AH.formatting))
                print("Formatted: Notation: {}; Labeling: {}; IEEE-488.2: {}; Field Width: {}.".format(*AH.formatting))
                self.bridge.write("UNITS {}".format(AH.units))
                print("Set units to {}.".format(AH.units))
            else:
                msgout = "error"
        else:
            msgout = f'Did not give a valid device id: {dev_id}'
        return msgout

    def run(self):
        """Establishes a socket server which takes and handles commands"""
        self.running = True
        # open a new socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.host_port)

            # confirm the socket is bound
            print(f"Socket bound to port: {self.host_port[1]}")

            # put the socket into listening mode
            s.listen()

            # loop until a client requests the server shutdown
            while self.running:
                # establish a connection with a client
                conn, addr = s.accept()
                with conn:
                    print(f"\nConnected to: {addr[0]}:{addr[1]}  : {time.ctime(time.time())}")
                    while True:
                        msg_client = conn.recv(1024)
                        # print(repr(msg_client))
                        if not msg_client:
                            break
                        elif msg_client == GpibServer.shutdown_command:
                            print("Received shutdown command")
                            self.running = False
                            break
                        else:
                            msg_client = msg_client.decode()
                            print(f"Received message: {msg_client}")
                            msg_server = self.handle(msg_client)
                            print(f"Sending back message: {msg_server}")
                            conn.sendall(msg_server.encode())


if __name__ == "__main__":
    import sys

    bridge_model, ls_model = sys.argv[1:3]

    server = GpibServer(bridge_model, int(ls_model))
    server.run()
