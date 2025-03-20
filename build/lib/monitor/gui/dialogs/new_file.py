"""
Dialog for creating new file for taking data

@author: Teddy Tortorici
"""

from PySide6.QtWidgets import (QDialog, QWidget, QGroupBox, QComboBox, QLineEdit, QDialogButtonBox, QFileDialog,
                               QLabel, QSpinBox, QPushButton, QFormLayout, QVBoxLayout, QDoubleSpinBox, QStackedWidget)
from PySide6.QtCore import Slot
import gui.icons as icon
import sys
import yaml
import os
import glob
import datetime
import time


def datetime_from_yaml_name(yaml_name):
    return datetime.datetime.fromisoformat(yaml_name.split(os.sep)[-1].lstrip('presets').rstrip('.yml'))


class DropDown(QComboBox):
    def __init__(self, choices: list[str], shortcuts: list[str | int] = None, label: str = "", whats_this: str = None,
                 default_value: str | int = None):
        """
        ComboBox with label and stores it's own information
        :param label: a string that will be placed before the combobox in the form
        :param choices: The labels of the options that appear in the combo box
        :param shortcuts: option shortcuts for storing
        :param whats_this: description
        """
        super(self.__class__, self).__init__()
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        self.choices = choices
        self.shortcuts = shortcuts
        self.addItems(choices)
        if default_value is not None:
            self.set(default_value)

    def get(self) -> str:
        """
        Get the active entry
        :return: returns the shortcut of the selection if there are shortcuts. Otherwise, it returns the actual value
        """
        if self.shortcuts:
            return self.shortcuts[self.currentIndex()]
        else:
            return self.choices[self.currentIndex()]

    def set(self, option):
        """
        Sets the combobox option based off the shortcut given. If there aren't shortcuts, then it takes the actual value
        instead
        :param option: shortcut or box value
        """
        try:
            self.setCurrentIndex(self.shortcuts.index(option))
        except ValueError:
            self.setCurrentIndex(self.choices.index(option))


class TextEntry(QLineEdit):
    def __init__(self, label: str = "", whats_this: str = None, default_value: str = None):
        """
        Create a line edit entry box
        :param label: label to go next to it
        :param whats_this: description
        """
        super(self.__class__, self).__init__()
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        if default_value is not None:
            self.set(default_value)

    def get(self) -> str:
        """
        get the text that has been entered by the user
        :return: user entered text
        """
        return self.text()

    def set(self, text: str):
        """
        set the text of the box from the software. Overrides current text
        :param text: text to write
        """
        self.setText(text)


class IntListBox(QLineEdit):
    def __init__(self, label: str = "", whats_this: str = None, default_value: list = None):
        """
        Create a line edit entry box that converts comma delimited text into a list of ints
        :param label: label to go next to it.
        :param whats_this: description
        """
        super(self.__class__, self).__init__()
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        if default_value is not None:
            self.set(default_value)

    def get(self) -> list:
        """
        get the text that has been entered by the user
        :return: user entered text
        """
        return [int(float(entry)) for entry in self.text().split(",")]

    def set(self, list_of_ints: list):
        """
        set the text of the box from the software. Overrides current text
        :param list_of_ints: writes list as a string
        """
        self.setText(str(list_of_ints).lstrip("[").rstrip("]"))


class FileButton(QPushButton):
    def __init__(self, base_path: str, title: str = "", label: str = "",
                 whats_this: str = None, filetypes: str = "CSV (*.csv)", default_value: str = None):
        """
        Create a button for opening a file
        :param base_path: base path for file dialog
        :param title: Default text of button (and title of dialog window)
        :param label: text to the side
        :param whats_this: description
        :param filetypes: types of files to filter separated by ';;'
        """
        super(self.__class__, self).__init__()
        self.base_path = base_path
        self.title = title
        self.setText(title)
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        self.filetypes = filetypes

        self.filename = None

        self.clicked.connect(self.open_file)

        if default_value is not None:
            self.set(default_value)

    @Slot()
    def open_file(self):
        """
        Open file dialog and replace button text with the filename
        """
        self.filename, _ = QFileDialog.getOpenFileName(self, self.title, self.base_path,
                                                       f"{self.filetypes};;All Files (*)")
        filename_display = self.filename.lstrip(self.base_path)
        self.set(filename_display)

    def get(self) -> str:
        """
        Get the filepath
        :return: Will return the filepath given from the button
        """
        if self.filename:
            return self.filename
        elif self.text() == self.title or not self.text():
            return ""
        else:
            return os.path.join(self.base_path, self.text())

    def set(self, text: str):
        if text:
            self.setText(text)
        else:
            self.setText(self.title)


class IntBox(QSpinBox):
    def __init__(self, label: str = "", whats_this: str = None, default_value: int = None):
        """
        Create a spinbox for entering integer values
        :param label: Label to the left
        :param whatsthis: Description
        """
        super(self.__class__, self).__init__()
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        if default_value is not None:
            self.set(default_value)

    def get(self) -> int:
        """
        return the integer value
        :return: The user defined value
        """
        return self.value()

    def set(self, value: int):
        """
        Sets the value in the box
        :param value: an integer value to display
        """
        self.setValue(value)


class FloatBox(QDoubleSpinBox):
    def __init__(self, precision: int = 1, minimum: float = 0., maximum: float = 100., step_size: float = 1.,
                 label: str = "", whats_this: str = None, default_value: float = None):
        super(self.__class__, self).__init__()
        self.setDecimals(precision)
        self.setMaximum(maximum)
        self.setMinimum(minimum)
        self.setSingleStep(step_size)
        self.label = QLabel(label + ":")
        if whats_this:
            self.label.setWhatsThis(whats_this)
        if default_value is not None:
            self.set(default_value)

    def get(self) -> float:
        """
        Get the float value stored in the box
        :return: the float value given by the user
        """
        return self.value()

    def set(self, value: float):
        """
        Set the value in the box
        :param value: set the float value in the box
        """
        self.setValue(value)


class NewFileDialog(QDialog):
    def __init__(self, base_path):
        """
        Create a form dialog box that you can fill out to prompt the code with the details of a new dataset
        :param base_path: base path to data
        """
        super(self.__class__, self).__init__()
        self.base_path = base_path
        self.date = None        # will fill once Okay is hit
        self.setWindowTitle("Measurement Details")
        self.setWindowIcon(icon.built_in(self, 'MessageBoxQuestion'))
        with open(os.path.join("gui", "stylesheets", "main.css"), "r") as f:
            self.setStyleSheet(f.read())

        """DEFAULT VALUES"""
        self.presets = {}
        self.bridge_choice = "AH"
        self.ls_choice = 331
        self.purp_choice = "TEST"
        self.chip_id = ""
        self.sample = ""
        self.frequencies = [400, 1400, 14000]
        self.calibration_path = ""
        self.film_thickness = 0.
        self.voltage = 1.
        self.averaging = 7
        self.dc_bias_setting = "OFF"
        self.dc_bias_voltage = 0.
        self.amplification = 0.
        self.comment = ""

        """OVERRIDE PRESETS FROM MOST RECENT YAML FILE"""
        try:
            self.load_yaml()
        except ValueError:      # no presets
            pass

        """CREATE FORM ENTRY BOXES"""
        # ALWAYS
        self.purp_box = DropDown(choices=["Calibration", "Powder Sample",
                                          "Thin Film", "Other", "Test"],
                                 shortcuts=["CAL", "POW", "FILM", "OTHER", "TEST"],
                                 label="Purpose of Measurement",
                                 whats_this="What kind of measurement is this",
                                 default_value=self.purp_choice)
        self.bridge_box = DropDown(choices=["Andeen-Hagerling 2500A", "Hewlett Packard 4275", "Fake"],
                                   shortcuts=["AH", "HP", "FAKE"],
                                   label="Capacitance Bridge",
                                   whats_this="What capacitance bridge model are you interacting with?",
                                   default_value=self.bridge_choice)
        self.ls_box = DropDown(choices=["LS331", "LS340"],
                               shortcuts=[331, 340],
                               label="Temperature Controller being used",
                               whats_this="Which Lakeshore Temperature Controller is being used?",
                               default_value=self.ls_choice)
        self.frequency_box = IntListBox(label="Frequencies to measure at",
                                        whats_this="Type frequencies in Hz separated by commas",
                                        default_value=self.frequencies)
        self.voltage_box = FloatBox(precision=2,
                                    maximum=15.,
                                    label="Measurement Voltage [V]",
                                    whats_this="Maximum test voltage of the AH. Not used by the HP bridge",
                                    default_value=self.voltage)
        self.ave_box = IntBox(label="Averaging Setting",
                              whats_this="On the AH this corresponds to an averaging time. On the HP, it will be the"
                                         "number of measurements to average.",
                              default_value=self.averaging)
        self.dc_bias_setting_box = DropDown(choices=["Off", "On: Low Current", "On: High Current"],
                                            shortcuts=["OFF", "LOW", "HIGH"],
                                            label="DC Bias Setting",
                                            whats_this="Enables or disables a user-supplied DC bias voltage of up to"
                                                       "±100 VDC to be applied to the measured unknown. The external"
                                                       "source is connected to the rear panel DC BIAS input. This"
                                                       "command also selects the value of an internal resistor"
                                                       "that is placed in series with the externally applied voltage"
                                                       "source.",
                                            default_value=self.dc_bias_setting)
        self.dc_bias_value_box = FloatBox(precision=2,
                                          maximum=100.,
                                          label="DC Bias Voltage Amount [V]",
                                          whats_this="If you are using the DC Bias, what is the value of the voltage"
                                                     "that you will bias with.",
                                          default_value=self.dc_bias_voltage)
        self.amp_box = FloatBox(precision=2,
                                maximum=1000.,
                                label="DC Bias Amplification",
                                whats_this="Value of the amplification being used for the DC Bias.",
                                default_value=self.amplification)
        self.comment_box = TextEntry(label="Comment",
                                     whats_this="Any comment you would like to add at the header of the file.",
                                     default_value=self.comment)

        # FOR SAMPLES
        self.chip_id_box = TextEntry(label="Capacitor Chip ID",
                                     whats_this="This is the identifier for the capacitor being used",
                                     default_value=self.chip_id)
        self.sample_box = TextEntry(label="Sample Name",
                                    whats_this="Name of sample",
                                    default_value=self.sample)

        # FOR FILMS
        self.cal_file_box = FileButton(base_path=os.path.join(base_path, "1-Calibrations"),
                                       title="Locate Calibration File",
                                       label="Path to Calibration File",
                                       whats_this="This is used for film measurements to remove the background and"
                                                  "reveal the dielectric constant",
                                       default_value=self.calibration_path)
        self.film_thickness_box = FloatBox(precision=6,
                                           maximum=10.,
                                           step_size=0.001,
                                           label="Film Thickness [\u03BCm]",
                                           whats_this="Thickness of the film in microns",
                                           default_value=self.film_thickness)
        self.gap_width_box = FloatBox(precision=1,
                                      maximum=20.,
                                      label="Gap Width")

        boxes = [self.purp_box, self.bridge_box, self.ls_box, self.frequency_box, self.chip_id_box, self.sample_box,
                 self.voltage_box, self.ave_box, self.cal_file_box, self.film_thickness_box, self.dc_bias_setting_box,
                 self.dc_bias_value_box, self.amp_box, self.comment_box]

        """GENERATE FORM"""
        self.form = QGroupBox("Enter measurement details for the dataset")

        form_layout = QFormLayout()

        for box in boxes:
            form_layout.addRow(box.label, box)
        self.form.setLayout(form_layout)

        """PLACE BUTTONS IN THE BOX"""
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_click)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.form)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def load_yaml(self):
        """
        Load presets
        """
        yaml_fname = max(glob.glob(os.path.join(self.base_path, "presets", "*yml")),
                         key=datetime_from_yaml_name)
        yaml_f = os.path.join(self.base_path, "presets", yaml_fname)
        print(f"found yaml: {yaml_f}")
        with open(yaml_f, 'r') as f:
            preset = yaml.safe_load(f)

        self.bridge_choice = preset['bridge']
        self.ls_choice = preset['ls']
        self.purp_choice = preset['purp']
        self.chip_id = preset['id']
        self.sample = preset['sample']
        self.frequencies = preset['freqs']
        self.calibration_path = preset['cal']
        self.film_thickness = preset['filmT']
        self.voltage = preset['v']
        self.averaging = preset['ave']
        self.dc_bias_setting = preset['dc']
        self.dc_bias_voltage = preset['dcv']
        self.amplification = preset['amp']
        self.comment = preset['comment']

    def save_yaml(self):
        """
        Save Presets
        """
        self.presets = {'bridge': self.bridge_choice,
                        'ls': self.ls_choice,
                        'purp': self.purp_choice,
                        'id': self.chip_id,
                        'sample': self.sample,
                        'freqs': self.frequencies,
                        'cal': self.calibration_path,
                        'filmT': self.film_thickness,
                        'v': self.voltage,
                        'ave': self.averaging,
                        'dc': self.dc_bias_setting,
                        'dcv': self.dc_bias_voltage,
                        'amp': self.amplification,
                        'lj': [0, 0, 0, 0],
                        'comment': self.comment}

        save_name = f'presets{self.date.year:04}-{self.date.month:02}-{self.date.day:02}_{self.date.hour:02}.yml'
        save_presets = os.path.join(self.base_path, "presets", save_name)
        with open(save_presets, 'w') as f:
            yaml.dump(self.presets, f, default_flow_style=False)

    def accept_click(self):
        """
        What happens when you click accept
        """
        self.date = datetime.datetime.fromtimestamp(time.time())
        self.bridge_choice = self.bridge_box.get()
        self.ls_choice = self.ls_box.get()
        self.purp_choice = self.purp_box.get()
        self.chip_id = self.chip_id_box.get()
        self.sample = self.sample_box.get()
        self.frequencies = self.frequency_box.get()
        self.calibration_path = self.cal_file_box.get()
        self.film_thickness = self.film_thickness_box.get()
        self.voltage = self.voltage_box.get()
        self.averaging = self.ave_box.get()
        self.dc_bias_setting = self.dc_bias_setting_box.get()
        self.dc_bias_voltage = self.dc_bias_value_box.get()
        self.amplification = self.amp_box.get()
        self.comment = self.comment_box.get()
        self.save_yaml()
        self.accept()


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import get

    app = QApplication(sys.argv)
    dialog = NewFileDialog(os.path.join(get.google_drive(), 'Dielectric_data', 'Teddy-2'))
    sys.exit(dialog.exec())
