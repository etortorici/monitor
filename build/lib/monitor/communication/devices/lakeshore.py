"""
classes for communicating with Lakeshore temperature controllers

@author: Teddy Tortorici
"""

import numpy as np
from monitor.communication.socket_client import Device


class Client(Device):
    def __init__(self, model_num: int):
        """
        Objects will send commands to the socket server to handle GPIB commands
        :param model_num: lakeshore model number
        """
        super(self.__class__, self).__init__("LS")
        self.inst_num = model_num

        self.ramp_speed = None

        # create list of heater range values in Watts
        # The index is the setting value on the instrument
        # The element corresponding to that index is the power in Watts
        if model_num == 340:
            self.heater_ranges = np.array([0.0, 0.05, 0.5, 5.0, 50.0])
        else:
            self.heater_ranges = np.array([0.0, 0.5, 5.0, 50.0])
        # Get PID values set on channel 1 and 2. the 0th entry is a dummy, since the loops index from 1
        self.PID = [0, self.read_pid(1), self.read_pid(2)]

        # Make sure control loop settings are in Kelvin and based on channel A
        self.set_control_loop()

    def read_front_panel(self) -> tuple[str, str]:
        """
        Read temperature from both stages in Kelvin
        :return: [Stage A, Stage B] temperatures
        """
        temperature_a = self.query(f'KRDG? A').strip("+")
        temperature_b = self.query(f'KRDG? B').strip("+")
        return temperature_a, temperature_b

    def read_heater_output(self) -> str:
        """
        Query the percent power being output to the heater
        :return: in percent
        """
        return self.query('HTR?')

    def read_heater_range(self) -> float:
        """
        Query the heater range.
        :return: Heater range setting in Watts
        """
        return float(self.heater_ranges[int(self.query('RANGE?'))])

    def read_pid(self, loop: int = 1) -> tuple:
        """
        Returns in units of Kelvin per minute
        :param loop: either PID loop 1 or 2 on the device
        :return: (P, I, D)
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        msg_back = self.query(f"PID? {int(loop):d}")
        pid = [float(element) for element in msg_back.split(',')]
        return tuple(pid)

    def read_ramp_speed(self, loop: int = 1) -> float:
        """
        read the ramping speed setting Kelvin per minute
        :param loop: either PID loop 1 or 2 on the device
        :return: the rate at which the setpoint moves when adjusted in K/min
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        self.ramp_speed = float(self.query(f"RAMP? {loop:d}").split(',')[1])
        return self.ramp_speed

    def read_ramp_status(self, loop: int = 1) -> int:
        """
        Check whether the setpoint is ramping or not
        :param loop: either PID loop 1 or 2 on the device
        :return: 0 or 1 boolean value of whether or not the device is ramping (is the setpoint moving?)
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        return int(self.query(f"RAMPST? {loop:d}"))

    def read_setpoint(self, loop: int = 1) -> float:
        """
        Read the temperature setpoint for the PID loop
        :param loop: either PID loop 1 or 2 on the device
        :return: the temperature that the PID loop tries to hold the temperature to
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        return float(self.query(f"SETP? {loop:d}"))

    def read_temperature(self, channel: str = 'A', units: str = 'K') -> float:
        """
        Read the temperature reading for the thermometer on a particular channel
        :param channel: A or B
        :param units: K or C or S (for sensor)
        :return: tempurature on the requested channel
        """
        # Ensure the variables are uppercase
        channel = channel.upper()
        units = units.upper()

        # Ensure the variables are valid
        if channel not in ['A', 'B']:
            raise ValueError(f"Invalid channel: {channel:s}")
        if units not in ['K', 'C', 'S']:
            raise ValueError(f"Invalid units: {units:s}")
        return float(self.query(f"{units:s}RDG? {channel:s}"))

    def set_control_loop(self, loop: int = 1, channel: str = "A", units: str = "K", powerup_enable: bool = True):
        """
        Change the settings of a PID control loop
        :param loop: Which loop to configure (1 or 2)
        :param channel: Which input channel to control from (A or B)
        :param units: what units to use for the setpoint (K, C, or S), S for sensor units
        :param powerup_enable: wheter the control loop is on or off after power-up
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        if channel not in ['A', 'B']:
            raise ValueError(f"Invalid channel: {channel}")
        unit_settings = ["", 'K', 'C', 'S']
        unit_setting = unit_settings.index(units[0].upper())
        self.write(f"CSET {loop:d}, {channel:s}, {unit_setting:d}, {powerup_enable:b}, 1")

    def set_heater_range(self, power_range: float, override: bool = False):
        """
        Sets the maximum amount of power that will be output to the heater
        :param power_range: range in Watts
        :param override: 50 W will break solder joints, setting this to True will allow you to set 50 W, otherwise, it won't let you.
        """
        # ensure that the power_range is positive
        power_range = abs(float(power_range))

        # find the nearest valid setting to the power given
        setting = np.argmin(self.heater_ranges - power_range)
        if self.heater_ranges[setting] == 50. and not override:
            print("50 W is probably too high and will fry your solder joints. If you disagree, override==True")
        else:
            self.write(f"RANGE {setting}")

    def heater_off(self):
        """
        Use set_heater_range() to turn off the heater
        """
        self.set_heater_range(0)

    def set_pid(self, proportional: float = None, integral: float = None, derivative: float = None, loop: int = 1):
        """
        Sets PID control values on loop 1 or 2
        :param proportional: proportional * error(T)
        :param integral: integral * integral_of(error(T) dT)
        :param derivative: derivative * d(error(T))/dT
        :param loop: either PID loop 1 or 2 on the device
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        if proportional is None:
            proportional = self.PID[loop][0]
        else:
            self.PID[loop][0] = float(proportional)
        if integral is None:
            integral = self.PID[loop][1]
        else:
            self.PID[loop][1] = float(integral)
        if derivative is None:
            derivative = self.PID[loop][2]
        else:
            self.PID[loop][2] = float(derivative)
        self.write(f"PID {loop:d}, {proportional:.2f}, {integral:.2f}, {derivative:.2f}")

    def set_ramp_speed(self, kelvin_per_min: float, loop: int = 1, ramping: bool = True):
        """
        Set the speed at which the setpoint changes
        :param kelvin_per_min: the ramp speed in K/min
        :param loop: either PID loop 1 or 2 on the device
        :param ramping: turn ramping on or off (if off it will just instantaneously jump to new setpoints)
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop:d}")
        self.write(f"RAMP {loop:d}, {ramping:b}, {kelvin_per_min}")
        self.read_ramp_speed(loop)

    def ramping_off(self, loop: int = 1):
        """
        Turn off ramping (so setpoint instaneously moves)
        :param loop: either PID loop 1 or 2 on the device
        """
        self.set_ramp_speed(0., loop=loop, ramping=False)

    def set_setpoint(self, value: float, loop: int = 1):
        """
        Change the desired setpoint temperature of a PID loop
        :param value: the value for the setpoint (in whatever units the setpoint is using)
        :param loop: either PID loop 1 or 2 on the device
        """
        if loop != 1 and loop != 2:
            raise ValueError(f"invalid loop: {loop}")
        self.write(f"SETP {loop}, {float(value)}")
