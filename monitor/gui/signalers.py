from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal


class Signaler(QWidget):
    """emits a signal to a activate a slot"""
    signal = Signal()          # can emit an empty signal


class MessageSignaler(QWidget):
    """emits a message to a connected slot allowing you to write to the text box
    GUI's hate being altered from threads, and this is a way to avoid the issues associated with that"""
    signal = Signal(str)       # can emit a signal containing a string


class ListSignaler(QWidget):
    """emits a list to a connected"""
    signal = Signal(list)
