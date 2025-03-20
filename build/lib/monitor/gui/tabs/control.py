"""
A tab widget for controlling devices in app.py

@author: Teddy Tortorici
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QPushButton, QLineEdit, QGridLayout, QHBoxLayout,
                               QComboBox, QLabel, QDoubleSpinBox, QMainWindow)
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QFont
import os
import threading


label_font = QFont("Arial", 16)


class ControlTab(QWidget):

    title_font = QFont("Arial", 20)

    def __init__(self, parent: QMainWindow):
        QWidget.__init__(self)
        self.parent = parent
        self.parent.data_tab.controller_signaler.signal.connect(self.update_values)

        """PULL DEVICES FROM self.parent.data_tab.data"""
        self.bridge = None
        self.ls = None

        main_layout = QVBoxLayout()

        """BRIDGE CONTROLS"""
        bridge_title = self.Title("Bridge Remote Control")
        main_layout.addWidget(bridge_title)

        self.average_box = AverageBox(self)
        main_layout.addLayout(self.average_box.row_layout)

        send_bridge_box = SendBox(self, "bridge")
        main_layout.addLayout(send_bridge_box.row_layout_1)
        main_layout.addLayout(send_bridge_box.row_layout_2)

        """LAKESHORE CONTROLS"""
        main_layout.addWidget(Padding(10))
        ls_title = self.Title("Lakeshore Remote Control")
        main_layout.addWidget(ls_title)

        self.heater_range_box = HeaterRangeBox(self)
        main_layout.addLayout(self.heater_range_box.row_layout)

        self.ramp_speed_box = RampSpeedBox(self)
        main_layout.addLayout(self.ramp_speed_box.row_layout)

        self.setpoint_box = SetpointBox(self)
        main_layout.addLayout(self.setpoint_box.row_layout)

        self.pid_box = PidBox(self)
        main_layout.addLayout(self.pid_box.row_layout_1)
        main_layout.addLayout(self.pid_box.row_layout_2)
        main_layout.addLayout(self.pid_box.row_layout_3)

        send_ls_box = SendBox(self, "ls")
        main_layout.addLayout(send_ls_box.row_layout_1)
        main_layout.addLayout(send_ls_box.row_layout_2)

        self.widgets = [self.average_box, self.heater_range_box, self.ramp_speed_box, self.setpoint_box, self.pid_box]

        self.setLayout(main_layout)

    def initialize_controller(self):
        self.bridge = self.parent.data_tab.data.bridge
        self.ls = self.parent.data_tab.data.ls

    @Slot(str)
    def update_values(self, message_from_file):
        list_vals = message_from_file.split("::")
        print(list_vals)
        heater_range_index = list_vals[0]
        ramp_speed = list_vals[1]
        heater_output = list_vals[2]
        setpoint = list_vals[3]
        p = list_vals[4]
        i = list_vals[5]
        d = list_vals[6]
        self.heater_range_box.setCurrentIndex(int(heater_range_index))
        self.ramp_speed_box.display.setText(ramp_speed)
        self.ramp_speed_box.on_display.setText(heater_output)
        self.setpoint_box.display.setText(setpoint)
        self.pid_box.p_box.display.setText(p)
        self.pid_box.i_box.display.setText(i)
        self.pid_box.d_box.display.setText(d)


    @Slot()
    def update_all(self):
        for widget in self.widgets:
            widget.update_value()

    class Title(QLabel):
        def __init__(self, text: str):
            """
            Create a title row
            :param text: Title's text
            """
            super(self.__class__, self).__init__(text)
            self.setAlignment(Qt.AlignCenter)
            self.setFont(ControlTab.title_font)


def read_stylesheet(stylesheet: str, bold: bool = False):
    with open(os.path.join("gui", "stylesheets", stylesheet), "r") as f:
        style_text = f.read()
    if bold:
        style_text = style_text.replace("}", "font-weight : bold;}")
    return style_text


class Label(QLabel):
    def __init__(self, text: str):
        """
        Create a label for an entry box
        :param text: The label's text
        """
        super(Label, self).__init__(text)
        self.setFont(label_font)
        self.setAlignment(Qt.AlignRight | Qt.AlignCenter)


class Padding(Label):
    def __init__(self, padding_px: int):
        super(Padding, self).__init__("")
        self.setFixedWidth(padding_px)


class DisplayValue(QLineEdit):

    def __init__(self):
        super(DisplayValue, self).__init__()
        self.setReadOnly(True)
        self.stylesheet = read_stylesheet("display.css")
        self.setStyleSheet(self.stylesheet)
        self.setAlignment(Qt.AlignCenter)

    def change_color(self, hex_color: str):
        """
        Change the background color of the display
        :param hex_color: must be #xaxaxa format
        """
        self.stylesheet[28:35] = self.stylesheet[:28] + hex_color + self.stylesheet[35:]
        self.setStyleSheet(self.stylesheet)


class RowLayout(QHBoxLayout):
    def __init__(self, widgets: list[QWidget], stretch: bool = False):
        super(RowLayout, self).__init__()
        if not stretch:
            self.addStretch(1)
        for widget in widgets:
            widget.setFont(label_font)
            self.addWidget(widget)


class SendBox(QLineEdit):
    def __init__(self, parent: ControlTab, device: str):
        """
        An entry box for sending raw messages directly to a device
        :param device: The device to send the message to
        """
        super(SendBox, self).__init__()
        self.setStyleSheet(read_stylesheet("input_line.css"))
        self.parent = parent
        self.device = device[0].upper()
        self.label_send = Label("Send Raw Message")
        self.label_send.setFixedWidth(200)
        self.send_button = QPushButton()
        self.send_button.setText('Send')
        # print(read_stylesheet("button.css", True))
        self.send_button.setStyleSheet(read_stylesheet("button.css", True))
        self.send_button.setFixedWidth(100)
        self.send_button.clicked.connect(self.send)
        self.clear_button = QPushButton()
        self.clear_button.setText('Clear')
        self.clear_button.setFixedWidth(100)
        self.clear_button.setStyleSheet(read_stylesheet("button.css"))
        self.clear_button.clicked.connect(self.clear_text)
        self.row_layout_1 = RowLayout([self.label_send, self, self.send_button, self.clear_button], True)

        self.label_response = Label("Last Response")
        self.label_response.setFixedWidth(200)
        self.response = DisplayValue()
        self.row_layout_2 = RowLayout([self.label_response, self.response], True)

    def setEnabled(self, arg__1: bool) -> None:
        super(SendBox, self).setEnabled(arg__1)
        self.send_button.setEnabled(arg__1)
        self.clear_button.setEnabled(arg__1)

    @Slot()
    def send(self):
        """
        Create a thread to send the message from
        """
        t = threading.Thread(target=self.send_thread, args=())
        t.start()

    def send_thread(self):
        """
        Send the text in the entry box to the device
        """
        self.send_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.response.setText("")

        msg_out = self.text()
        if msg_out:
            if self.device == "B":
                msg_back = self.parent.bridge.query(str(msg_out))
            elif self.device == "L":
                msg_back = self.parent.ls.query(str(msg_out))
            else:
                msg_back = "Something went wrong"
        else:
            msg_back = "Did not send anything"
        self.response.setText(str(msg_back))

        self.send_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    @Slot()
    def clear_text(self):
        """
        Clear the text in the entry box
        """
        self.setText("")


class ApplyButton(QPushButton):
    def __init__(self, apply_method):
        """
        Button for connecting to an "apply" method
        :param apply_method: a method built into the object that has this button in it
        """
        super(ApplyButton, self).__init__()
        self.setText("Apply")
        self.setStyleSheet(read_stylesheet("button.css", True))
        self.setFixedWidth(100)
        self.clicked.connect(apply_method)


class AverageBox(QSpinBox):
    def __init__(self, parent):
        super(AverageBox, self).__init__()
        self.parent = parent
        self.setMaximum(15)
        self.setFixedWidth(50)
        self.setStyleSheet(read_stylesheet("spinbox.css"))

        self.display = DisplayValue()
        self.display.setFixedWidth(50)

        self.apply_button = ApplyButton(self.apply)
        self.row_layout = RowLayout([Label("Averaging Setting"), self.display, Padding(50),
                                     Label("Change Setting"), self, self.apply_button])

    def setEnabled(self, arg__1: bool) -> None:
        super(AverageBox, self).setEnabled(arg__1)
        self.apply_button.setEnabled(arg__1)

    @Slot()
    def apply(self):
        t = threading.Thread(target=self.apply_thread, args=())
        t.start()

    def apply_thread(self):
        if self.isEnabled():
            self.apply_button.setEnabled(False)
            self.parent.bridge.set_ave(self.value())
            self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        self.display.setText(f"{self.parent.bridge.ave_setting:d}")


class HeaterRangeBox(QComboBox):
    def __init__(self, parent: ControlTab):
        super(HeaterRangeBox, self).__init__()
        self.setEditable(True)
        self.lineEdit().setAlignment(Qt.AlignCenter)
        self.setStyleSheet(read_stylesheet("combobox.css"))
        self.setFixedWidth(150)
        self.parent = parent

        self.choices = ["Off", "500 mW", "5 W"]
        self.range_values = dict(zip(self.choices, [0, 0.5, 5]))
        self.addItems(self.choices)
        self.activated.connect(self.apply)

        self.row_layout = RowLayout([Label("Heater Power Range"), self, Padding(450)])

    @Slot()
    def apply(self):
        """To allow the process to run in the background"""
        t = threading.Thread(target=self.apply_thread, args=())
        t.daemon = True         # makes it so if the main thread shuts down, you don't have to wait for this.
        t.start()

    def apply_thread(self):
        """What happens when you change the selection"""
        # Turn off buttons
        self.setEnabled(False)

        # print("Setting Heater")
        heater_choice = self.box.currentText()
        heater_range = self.range_values[heater_choice]
        self.parent.ls.set_heater_range(heater_range)
        # print(f"Set heater to {heater_choice}")

        self.setEnabled(True)

    @Slot()
    def update_value(self):
        """Run update in a thread"""
        t = threading.Thread(target=self.update_thread, args=())
        t.daemon = True
        t.start()

    def update_thread(self):
        """Thread to run for update"""
        self.setEnabled(False)
        hrange = self.parent.ls.read_heater_range()
        if hrange > 1:
            hstring = f'{int(hrange)} W'
        elif not hrange:
            hstring = 'Off'
        else:
            hstring = f'{int(hrange * 1000)} mW'
        self.setCurrentIndex(self.choices.index(hstring))
        self.setEnabled(True)


class SpinBoxTemplate(QDoubleSpinBox):
    def __init__(self, label: str | None, precision: int = 1, maximum: float = None, minimum: float = 0.):
        super(SpinBoxTemplate, self).__init__()
        self.setFixedWidth(100)
        self.setDecimals(precision)
        if maximum:
            self.setMaximum(maximum)
        self.setMinimum(minimum)

        self.display = DisplayValue()

        self.apply_button = ApplyButton(self.apply)

        if label is not None:
            self.row_layout = RowLayout([Label(label), self.display, Padding(50),
                                         Label("Change Setting"), self, self.apply_button])

    def setEnabled(self, arg__1: bool) -> None:
        super(SpinBoxTemplate, self).setEnabled(arg__1)
        self.apply_button.setEnabled(arg__1)

    @Slot()
    def apply(self):
        t = threading.Thread(target=self.apply_thread, args=())
        t.start()

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        pass


class RampSpeedBox(SpinBoxTemplate):
    def __init__(self, parent: ControlTab):
        super(RampSpeedBox, self).__init__(None, precision=1, maximum=100.0)
        self.parent = parent
        self.display.setFixedWidth(100)
        self.on_display = DisplayValue()
        self.on_display.setFixedWidth(50)
        self.percent_display = DisplayValue()
        self.percent_display.setFixedWidth(75)
        self.row_layout = RowLayout([Label("Ramp Speed (K/min)"), self.display, self.on_display, self.percent_display,
                                     Padding(50), Label("Change Setting"), self, self.apply_button])

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.parent.ls.set_ramp_speed(self.value())
        self.update_value()

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        self.display.setText(f"{self.parent.ls.ramp_speed:.1f}")
        ramp_status = self.parent.ls.read_ramp_status()
        self.on_display.change_color(["#6b1313", "#106324"][ramp_status])
        self.on_display.setText(["Off", "On"][ramp_status])
        self.percent_display.setText(self.parent.ls.read_heater_output + "%")


class SetpointBox(SpinBoxTemplate):
    def __init__(self, parent: ControlTab):
        super(self.__class__, self).__init__("Temperature Setpoint (K)", precision=2, maximum=400.00)
        self.parent = parent

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.parent.ls.set_setpoint(self.value())

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        setpoint = self.parent.ls.read_setpoint()
        self.display.setText(f"{setpoint:.2f}")


class PBox(SpinBoxTemplate):
    def __init__(self, parent: ControlTab):
        super(PBox, self).__init__("P", 1, 1000., .1)
        self.parent = parent

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.parent.ls.set_pid(proportional=self.value())

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        self.display.setText(f"{self.parent.ls.PID[1][0]:.2f}")


class IBox(SpinBoxTemplate):
    def __init__(self, parent: ControlTab):
        super(IBox, self).__init__("I", 1, 1000., 0.1)
        self.parent = parent

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.parent.ls.set_pid(integral=self.value())

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        self.display.setText(f"{self.parent.ls.PID[1][1]:.2f}")


class DBox(SpinBoxTemplate):
    def __init__(self, parent: ControlTab):
        super(DBox, self).__init__("D", 1, 200.)
        self.parent = parent

    def apply_thread(self):
        self.apply_button.setEnabled(False)

        self.parent.ls.set_pid(derivative=self.value())

        self.apply_button.setEnabled(True)

    @Slot()
    def update_value(self):
        self.display.setText(f"{self.parent.ls.PID[1][2]:.2f}")


class PidBox:
    def __init__(self, parent: ControlTab):
        self.parent = parent
        self.p_box = PBox(parent)
        self.i_box = IBox(parent)
        self.d_box = DBox(parent)
        labels = [Label("P"), Label("I"), Label("D")]

        for box, label in zip([self.p_box, self.i_box, self.d_box], labels):
            box.display.setFixedWidth(120)
            label.setFixedWidth(15)
            label.setAlignment(Qt.AlignCenter)

        self.row_layout_1 = RowLayout([Label("PID Values"), self.p_box.display, self.i_box.display, self.d_box.display,
                                       Padding(100), labels[0], self.p_box, self.p_box.apply_button])
        self.row_layout_2 = RowLayout([labels[1], self.i_box, self.i_box.apply_button])
        self.row_layout_3 = RowLayout([labels[2], self.d_box, self.d_box.apply_button])

    @Slot()
    def update_value(self):
        self.p_box.update_value()
        self.i_box.update_value()
        self.d_box.update_value()


#class MessageBox(BoxTemplate, QLineEdit):
#    def __init__(self, parent: ControlTab):
#        super(self.__class__, self).__init__(self)
#        self.parent = parent
#        self.button.setText("Send")             # Change button from Set to Send
#
#        # add a clear button
#        self.clear_button = QPushButton()
#        self.clear_button.setText("Clear")
#        self.clear_button.setFixedWidth(100)
#        self.return_box = QLineEdit()
#        self.return_box.setReadOnly(True)
#
#    def set_thread(self):
#        pass
#
#
#if __name__ == "__main__":
#    import sys
#    from PySide6.QtWidgets import QApplication
#    sys.path.append("..\\..")
#    app = QApplication(sys.argv)
#
#    main_window = ControlTab(0)
#    main_window.show()
#
#    sys.exit(app.exec())
#