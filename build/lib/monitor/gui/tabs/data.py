"""
A tab widget for taking data in app.py

@author: Teddy Tortorici
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QSizePolicy,
                               QDialog, QMessageBox, QFileDialog, QMainWindow)
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont
from gui.dialogs.new_file import NewFileDialog
import gui.icons as icon
from gui.signalers import Signaler, MessageSignaler
from gui.text_stream import TextStream
from files.data import DielectricSpec as data_files
from communication import GpibServer
from communication.socket_client import send as send_client
from calculations.calibration import Calibration
import threading
import time
import ast
import os


class DataTab(QWidget):
    font = QFont("Arial", 12)

    def __init__(self, parent: QMainWindow):
        """
        Tab for managing the current data file
        :param parent: Is the MainWindow() object
        """
        QWidget.__init__(self)
        self.parent = parent

        self.gpib_server = None

        self.dialog = None
        self.data = None  # will be an object of a data file from data_file2.py

        self.server_thread = None  # will create thread on data file start up
        self.data_thread = None  # will create thread on data file start up
        self.path = None
        self.filename = None

        self.running = False
        self.active_file = False
        self.started = False

        """So we can update plots when new data is taken"""
        self.plot_updater = Signaler()
        self.plot_initializer = MessageSignaler()

        """So we can update controller"""
        self.update_controller = Signaler()
        # Moved to activate_data_file()
        # self.plot_updater = PlotUpdaterWidget()
        # self.plot_updater.update.connect(self.parent.plot_tab.update_plots)
        # self.plot_updater.initialize.connect(self.parent.plot_tab.initialize_plots)

        """Create the layout of what goes in this tab"""
        self.layout = QVBoxLayout(self)

        self.data_text_stream = TextStream(DataTab.font)  # this will be where data gets printed as it's collected

        self.bottom_row = QHBoxLayout()  # this will be a row to add widgets to bellow the text stream
        self.bottom_row.addStretch(1)

        self.button_new_data = QPushButton("Create New Data File")
        self.button_new_data.setIcon(icon.built_in(self, 'FileIcon'))
        self.button_new_data.clicked.connect(self.make_new_file)

        self.button_open_data = QPushButton("Open Data File")
        self.button_open_data.setIcon(icon.built_in(self, 'DirIcon'))
        self.button_open_data.clicked.connect(self.open_file)

        self.button_play_pause = QStackedWidget(self)
        self.button_play_pause.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_pause = QPushButton("Pause Data")
        self.button_pause.setIcon(icon.custom("pause.png"))
        self.button_pause.clicked.connect(self.pause_data)
        self.button_play = QPushButton("Take Data")
        self.button_play.setIcon(icon.custom("play.png"))
        self.button_play.clicked.connect(self.continue_data)
        self.button_play.setEnabled(False)
        self.button_pause.setEnabled(False)
        self.button_play_pause.addWidget(self.button_play)
        self.button_play_pause.addWidget(self.button_pause)

        self.button_stop = QPushButton("Stop")
        self.button_stop.setIcon(icon.custom("stop.png"))
        self.button_stop.setEnabled(False)
        self.button_stop.clicked.connect(self.stop)

        # add bottom row widgets to bottom_row
        self.bottom_row.addWidget(self.button_stop)
        self.bottom_row.addWidget(self.button_play_pause)
        self.bottom_row.addWidget(self.button_open_data)
        self.bottom_row.addWidget(self.button_new_data)

        """Add widgets to layout"""
        self.layout.addWidget(self.data_text_stream)
        self.layout.addLayout(self.bottom_row)

        """So we can write to the GUI from threads"""
        self.writer_signaler = MessageSignaler()
        self.writer_signaler.signal.connect(self.data_text_stream.write)
        self.controller_signaler = MessageSignaler()


    def write(self, text: str, end: str = "\n"):
        """Writes to the GUI by using the write_thread widget"""
        # print(f'sending "{text}" to thread')
        self.writer_signaler.signal.emit(text + end)

    @Slot()
    def open_file(self):
        """Open a dialog to find a file to append to"""
        stopped = True
        if self.active_file:
            stopped = self.stop()
        if stopped:
            filepath, _ = QFileDialog.getOpenFileName(self.parent,  # parent
                                                      "Open data file",  # caption
                                                      self.parent.data_base_path,  # directory
                                                      "CSV (*.csv)")
            if filepath:
                # open file and read comment to find what the averaging setting is
                print(filepath)
                path = os.sep.join(filepath.split("/")[:-1])
                print(f"path{path}")
                filename = filepath.split("/")[-1]
                with open(filepath, 'r') as f:
                    for ii in range(2):  # number in range will be which line is stored at the end
                        comment_line = f.readline()

                self.dialog = FakeDialog(comment_line)  # with default averaging_entry = 1

                self.gpib_server = GpibServer(bridge_type=self.dialog.bridge_choice,
                                              ls_model=self.dialog.ls_choice,
                                              silent=True)

                self.write(f'Opening file "{filepath}"')
                self.write("Settings: " + comment_line.lstrip("# ").rstrip("\n"))

                self.activate_data_file(path, filename, start=False)
                if self.dialog.purp_choice == "FILM":
                    cal = Calibration(self.dialog.calibration_path)
                    self.data = data_files.DielectricConstant(path=path,
                                                              filename=filename,
                                                              frequencies=self.dialog.frequencies,
                                                              film_thickness=self.dialog.film_thickness,
                                                              capacitor_calibration=cal,
                                                              gui_signaler=self.writer_signaler,
                                                              con_signaler=self.controller_signaler,
                                                              bridge=self.dialog.bridge_choice,
                                                              ls_model=self.dialog.ls_choice)
                else:
                    self.data = data_files.DielectricSpec(path=path,
                                                          filename=filename,
                                                          frequencies=self.dialog.frequencies,
                                                          gui_signaler=self.writer_signaler,
                                                          con_signaler=self.controller_signaler,
                                                          bridge=self.dialog.bridge_choice,
                                                          ls_model=self.dialog.ls_choice)
                self.data.initiate_devices(voltage_rms=self.dialog.voltage,
                                           averaging_setting=self.dialog.averaging,
                                           dc_setting=self.dialog.dc_bias_setting)
                self.plot_initializer.signal.emit(os.path.join(path, filename))
                self.plot_updater.signal.emit()
                self.parent.control_tab.initialize_controller()

    @Slot()
    def make_new_file(self):
        """Open a dialog to create a new data file"""
        stopped = True
        if self.active_file:
            stopped = self.stop()
        if stopped:
            self.dialog = NewFileDialog(self.parent.data_base_path)
            self.dialog.exec()

            if self.dialog.result() == QDialog.Accepted:
                print("accepted dialog")
                bridge = self.dialog.bridge_choice
                ls_num = self.dialog.ls_choice
                cid = self.dialog.chip_id.replace(" ", "_")
                sample = self.dialog.sample.replace(" ", "_")
                cal_file = self.dialog.calibration_path
                print("get some dialog settings")

                self.gpib_server = GpibServer(bridge_type=bridge, ls_model=ls_num, silent=True)
                print("made server")
                creation_datetime = self.dialog.date
                self.write('Starting new data file on {m:02}/{d:02}/{y:04} at {h:02}:{min:02}:{s}'.format(
                    m=creation_datetime.month,
                    d=creation_datetime.day,
                    y=creation_datetime.year,
                    h=creation_datetime.hour,
                    min=creation_datetime.minute,
                    s=creation_datetime.second))

                """FIND PLACE TO WRITE FILE"""  # "Calibration", "Powder Sample", "Film Sample", "Other"
                path = self.parent.data_base_path
                if self.dialog.purp_choice == "CAL":
                    path = os.path.join(path, "1-Calibrations")
                elif self.dialog.purp_choice == "POW":
                    path = os.path.join(path, "2-Powders")
                elif self.dialog.purp_choice == "FILM":
                    path = os.path.join(path, "3-Films")
                elif self.dialog.purp_choice == "TEST":
                    path = os.path.join(path, "Tests")
                else:
                    path = os.path.join(path, "Other")
                path = os.path.join(path,
                                    str(creation_datetime.year),
                                    f"{creation_datetime.month} - {creation_datetime.strftime('%B')}")

                """CREATE FILENAME"""
                day = f"{creation_datetime.day:02}"
                year = f"{creation_datetime.year:04}"
                month = f"{creation_datetime.month:02}"
                start_time = f"{self.dialog.date.hour:02}-{self.dialog.date.minute:02}"
                print(self.dialog.date)
                print(start_time)
                if not sample:
                    sample = "Bare"
                if not cid:
                    cid = "test"
                filename = f"{year}-{month}-{day}__{sample}__{cid}__{bridge}__LS{ls_num}__T-{start_time}.csv"
                print(f"making file {filename}")

                """CREATE COMMENT LINE"""
                full_comment = str(self.dialog.presets)

                self.activate_data_file(path, filename)

                """Create data file"""
                if self.dialog.purp_choice == "FILM":
                    self.data = data_files.DielectricConstant(path=path,
                                                              filename=filename,
                                                              frequencies=self.dialog.frequencies,
                                                              film_thickness=self.dialog.film_thickness,
                                                              capacitor_calibration=Calibration(cal_file),
                                                              gui_signaler=self.writer_signaler,
                                                              con_signaler=self.controller_signaler,
                                                              bridge=bridge,
                                                              ls_model=ls_num,
                                                              comment=full_comment)
                else:
                    self.data = data_files.DielectricSpec(path=path,
                                                          filename=filename,
                                                          frequencies=self.dialog.frequencies,
                                                          gui_signaler=self.writer_signaler,
                                                          con_signaler=self.controller_signaler,
                                                          bridge=bridge,
                                                          ls_model=ls_num,
                                                          comment=full_comment)
                self.data.initiate_devices(voltage_rms=self.dialog.voltage,
                                           averaging_setting=self.dialog.averaging,
                                           dc_setting=self.dialog.dc_bias_setting)
                self.plot_initializer.signal.emit(os.path.join(path, filename))
                self.parent.control_tab.initialize_controller()
                self.start()

    def activate_data_file(self, path: str, filename: str, start: bool = True):
        """Whether we open a file or make a new one, we need to do all these things"""
        self.server_thread = threading.Thread(target=self.gpib_server.run, args=())
        self.server_thread.daemon = True
        self.data_thread = threading.Thread(target=self.take_data, args=())
        self.data_thread.daemon = True

        self.plot_updater.signal.connect(self.parent.plot_tab.update_plots)
        self.plot_initializer.signal.connect(self.parent.plot_tab.initialize_plots)
        self.update_controller.signal.connect(self.parent.control_tab.update_values)

        self.active_file = True
        self.button_play.setEnabled(not start)
        self.button_pause.setEnabled(start)
        self.button_stop.setEnabled(True)
        if start:
            self.button_play_pause.setCurrentWidget(self.button_pause)
        else:
            self.button_play_pause.setCurrentWidget(self.button_play)
        self.parent.play_action.setEnabled(not start)
        self.parent.pause_action.setEnabled(start)
        self.parent.stop_action.setEnabled(True)
        self.button_open_data.setEnabled(False)
        self.button_new_data.setEnabled(False)
        self.parent.open_file_action.setEnabled(False)
        self.parent.new_file_action.setEnabled(False)
        # self.parent.exit_action.setEnabled(False)

        """Start GPIB communication server"""
        self.server_thread.start()
        time.sleep(0.01)

    def start(self):
        self.started = True
        self.data_thread.start()

    def take_data(self):
        """This should be run in a thread"""
        self.running = True

        """INITIATE DEVICES WITH DIALOG SETTINGS"""
        print("setting devices")
        self.data.bridge.set_voltage(self.dialog.voltage)
        print("set voltage")
        self.data.bridge.set_ave(self.dialog.averaging)
        print("set ave")
        self.data.ls.set_ramp_speed(6.)
        print("set ramp speed")
        while self.active_file:
            while self.running:
                data_point = self.data.sweep_frequencies()
                # print(f'Got this as data: {data_point}')
                self.data.write_row(data_point)
                # self.write(str(data_point))
                if self.parent.plot_tab.live_plotting:
                    self.plot_updater.signal.emit()
                    self.update_controller.signal.emit()

    @Slot()
    def continue_data(self):
        """If data taking is paused, this will unpause it"""
        self.button_play_pause.setCurrentWidget(self.button_pause)
        self.button_pause.setEnabled(True)
        self.parent.pause_action.setEnabled(True)
        self.parent.play_action.setEnabled(False)
        if self.started:
            self.running = True
        else:
            self.start()

    @Slot()
    def pause_data(self):
        """Pause taking data"""
        self.button_play_pause.setCurrentWidget(self.button_play)
        self.button_play.setEnabled(True)
        self.parent.pause_action.setEnabled(False)
        self.parent.play_action.setEnabled(True)
        self.running = False
        self.write("Paused data taking.")

    @Slot()
    def stop(self):
        """Stop taking data and prepare to close or open or create new data"""
        exit_question = QMessageBox.question(self, 'Stop', 'Are you sure you would like to close this data file?',
                                             QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if exit_question == QMessageBox.Yes:
            self.write("Closing File")
            self.running = False
            self.active_file = False
            self.started = False
            # self.data_thread.start()
            # print('sldkfj')
            try:
                self.data_thread.join()
            except RuntimeError:
                pass
            self.button_stop.setEnabled(False)
            self.button_play_pause.setCurrentWidget(self.button_play)
            self.button_play.setEnabled(False)
            self.button_pause.setEnabled(False)
            self.parent.play_action.setEnabled(False)
            self.parent.pause_action.setEnabled(False)
            self.parent.stop_action.setEnabled(False)
            self.button_open_data.setEnabled(True)
            self.button_new_data.setEnabled(True)
            self.parent.open_file_action.setEnabled(True)
            self.parent.new_file_action.setEnabled(True)
            # self.parent.exit_action.setEnabled(False)
            send_client('shutdown')
            self.server_thread.join()
            self.data = None
            self.dialog = None
            self.filename = None
            self.path = None

            self.parent.plot_tab.plot_CvT.clear_plots()
            self.parent.plot_tab.plot_LvT.clear_plots()
            self.parent.plot_tab.plot_Tvt.clear_plots()
            self.parent.plot_tab.plot_Lvt.clear_plots()
            self.parent.plot_tab.plot_Cvt.clear_plots()
            return True
        else:
            return False


class FakeDialog:
    """This is for when we open a file so we can mimic pulling the averaging entry from the dialog for a new file"""

    def __init__(self, comment_line: str):
        preset = ast.literal_eval(comment_line.lstrip("# ").rstrip("\n"))
        self.preset = preset
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


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    main_window = DataTab(0)
    main_window.show()

    sys.exit(app.exec())
