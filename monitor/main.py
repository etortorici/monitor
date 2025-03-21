"""
Simple Monitor to mimic AH front panel

@author: Teddy Tortorici
"""

import sys
import threading
from pathlib import Path
import monitor.get as get
from monitor.communication.socket_client import shutdown_command
from monitor.communication.devices.lakeshore import Client as LakeShore
from PySide6.QtWidgets import (QMainWindow, QApplication, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QLabel, QRadioButton, QButtonGroup, QSpinBox, QDoubleSpinBox, QPushButton)
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QFont


STYLESHEETS = Path(__file__).resolve().parent / "gui" / "stylesheets"


class DisplayWidget(QLineEdit):
    def __init__(self, parent: QWidget, label: str = ""):
        super(DisplayWidget, self).__init__()
        self.parent = parent
        with open(STYLESHEETS / "display.css", "r") as f:
            self.setStyleSheet(f.read())

        self.setFont(QFont("Arial", 26))
        self.label = QLabel(label)
        self.label.setFixedWidth(225)
        self.label.setFont(QFont("Arial", 26))
        self.label.setAlignment(Qt.AlignCenter)

        self.setReadOnly(True)
        self.setAlignment(Qt.AlignRight)
        self.row_layout = QHBoxLayout()
        self.row_layout.addWidget(self.label)
        self.row_layout.addWidget(self)


class InputWidget(QLineEdit):
    def __init__(self, parent):
        super(InputWidget, self).__init__()
        self.parent = parent
        with open(STYLESHEETS / "input_line.css", "r") as f:
            self.setStyleSheet(f.read())


class FrequencyWidget(QButtonGroup):
    def __init__(self, parent):
        super(FrequencyWidget, self).__init__()
        self.parent = parent
        options = ("100 Hz", "400 Hz", "500 Hz", "600 Hz", "700 Hz", "800 Hz",
                   "1 kHz", "1.4 kHz", "1.6 kHz", "2 kHz", "2.4 kHz", "4 kHz",
                   "10 kHz", "12 kHz", "14 kHz", "16 kHz", "20 kHz")
        self.buttons = [None] * len(options)

        self.col_layout = QVBoxLayout()
        self.col_layout.setAlignment(Qt.AlignCenter)
        for ii, option in enumerate(options):
            widget = QRadioButton(option)
            if option in ("400 Hz", "1.4 kHz", "14 kHz"):
                widget.setStyleSheet("color: #FFFFAA; font: bold; font-size: 18px;")
            else:
                widget.setStyleSheet("color: #FFFFFF; font: arial; font-size: 18px;")
            self.buttons[ii] = widget
            self.addButton(widget, ii)
            self.col_layout.addWidget(widget)
        self.buttons[7].setChecked(True)
        self.buttonClicked.connect(self.button_press)

    @Slot()
    def button_press(self):
        new_frequency = self.value()
        # self.parent.bridge.write(f"FR {new_frequency:d}")
        print(f"Set frequency to {new_frequency}")

    def value(self):
        text = self.button(self.checkedId()).text().rstrip("Hz")
        if text[-1] == "k":
            frequency = int(float(text.rstrip(" k")) * 1000)
        else:
            frequency = int(text)
        return frequency


class AveragingWidget(QSpinBox):

    stepChanged = Signal()

    def __init__(self, parent: QWidget):
        super(AveragingWidget, self).__init__()
        self.label = QLabel("Averaging")
        self.label.setFont(QFont("Arial", 26))
        self.label.setAlignment(Qt.AlignCenter)

        self.setFont(QFont("Arial", 26))
        self.parent = parent
        self.setMinimum(0)
        self.setMaximum(15)
        self.setFixedWidth(100)

        # self.valueChanged.connect(self.set)
        self.editingFinished.connect(self.set)
        # self.stepChanged.connect(self.set)
        # self.lineEdit().setReadOnly(True)
        self.memory = 0

    @Slot()
    def set(self):
        new_ave_setting = self.value()
        if new_ave_setting != self.memory:
            # self.parent.bridge.set_ave(new_ave_setting)
            print(f"Setting Averaging to: {new_ave_setting}")
            self.memory = new_ave_setting

    # def stepBy(self, step):
    #     value = self.value()
    #     super(AveragingWidget, self).stepBy(step)
    #     if self.value() != value:
    #         self.stepChanged.emit()


class VoltageWidget(QDoubleSpinBox):
    def __init__(self, parent: QWidget, default_value: int = 1):
        super(VoltageWidget, self).__init__()
        self.parent = parent
        self.label = QLabel("Voltage RMS")
        self.label.setFont(QFont("Arial", 26))
        self.label.setAlignment(Qt.AlignCenter)

        self.setFont(QFont("Arial", 26))
        self.parent = parent
        self.setValue(default_value)
        self.memory = default_value
        self.setDecimals(3)
        self.setMinimum(0.001)
        self.setMaximum(15)
        self.setFixedWidth(200)

        self.editingFinished.connect(self.set)

    @Slot()
    def set(self):
        new_voltage = self.value()
        if new_voltage != self.memory:
            # self.parent.bridge.set_voltage(new_voltage)
            print(f"Set voltage {new_voltage}")
            self.memory = new_voltage


class MainWidget(QWidget):
    def __init__(self, model_number=340):
        super(MainWidget, self).__init__()

        self.run_thread = threading.Thread(target=self.run)
        self.run_thread.daemon = True

        self.lakeshore = LakeShore(model_number)

        main_layout = QHBoxLayout(self)

        display_layout = QVBoxLayout()

        display_keys = ("Temperature A", "Temperature B", "Heater", "Setpoint", "Ramp rate")
        self.displays = dict(zip(display_keys, [DisplayWidget(self, key) for key in display_keys]))

        for key in display_keys:
            display_layout.addLayout(self.displays[key].row_layout)

        # bottom_row = QHBoxLayout()
        # averaging_box = AveragingWidget(self)
        # voltage_box = VoltageWidget(self)
        # label = QLabel("press ENTER to set")
        # 
        # bottom_row.addWidget(label)
        # bottom_row.addWidget(averaging_box.label)
        # bottom_row.addWidget(averaging_box)
        # bottom_row.addWidget(voltage_box.label)
        # bottom_row.addWidget(voltage_box)
        # 
        # display_layout.addLayout(bottom_row)
        # 
        # self.frequency_options = FrequencyWidget(self)
        # 
        main_layout.addLayout(display_layout)
        # main_layout.addLayout(self.frequency_options.col_layout)

        self.setLayout(main_layout)
        self.run_thread.start()

    def update_displays(self, unit: str = "K"):
        unit = unit.upper()
        temperature_a = self.lakeshore.read_temperature("A", unit)
        temperature_b = self.lakeshore.read_temperature("B", unit)
        heater = self.lakeshore.read_heater_output()
        heater_range = self.lakeshore.read_heater_range()
        setpoint = self.lakeshore.read_setpoint()
        ramp_rate = self.lakeshore.read_ramp_speed()

        self.displays["Temperature A"].setText(f"{temperature_a:.2f} {unit}")
        self.displays["Temperature B"].setText(f"{temperature_b:.2f} {unit}")
        self.displays["Heater"].setText(f"{heater}% of {heater_range:.4f} W")
        self.displays["Setpoint"].setText(f"{setpoint:.2f} K")
        self.displays["Ramp rate"].setText(f"{ramp_rate} K/min")

    def run(self):
        while True:
            # front_panel = self.bridge.read_front_panel_full()
            self.update_displays()
            pass


class MainWindow(QMainWindow):
    width = 1200
    height = 650

    def __init__(self):
        """
        Main window that contains 3 tabs in a navigation widget. These tabs are for taking data, plotting data,
        and controlling devices.
        """
        QMainWindow.__init__(self)

        with open(STYLESHEETS / "main.css", "r") as f:
            self.setStyleSheet(f.read())

        self.force_quit = True  # when quit properly, this will be changed to false
        self.file_open = False

        """WINDOW PROPERTIES"""
        self.setWindowTitle("Data Acquisition App")
        self.resize(MainWindow.width, MainWindow.height)

        self.main = MainWidget()
        self.setCentralWidget(self.main)

    @Slot()
    def quit(self):
        """Exit program"""
        exit_question = QMessageBox.critical(self, 'Exiting', 'Are you sure you would like to quit?',
                                             QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if exit_question == QMessageBox.Yes:
            shutdown_command("localhost", get.port())
            self.force_quit = False
            print('Exiting')
            self.close()

    @Slot()
    def closeEvent(self, event):
        """Overrides closeEvent so that there is no force quit"""
        if self.force_quit:
            event.ignore()
            self.quit()
        else:
            event.accept()

    @Slot()
    def get_help(self):
        """Opens HELP Prompt"""
        self.help.exec()


if __name__ == "__main__":
    from monitor.communication.server import GpibServer
    from threading import Thread    
    server = GpibServer(None, None)#int(340))
    server_thread = Thread(target=server.run, args=())
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
