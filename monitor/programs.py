import monitor.main as monitor
import sys
from PySide6.QtWidgets import QApplication


def lakeshore():
    app = QApplication(sys.argv)

    main_window = monitor.MainWindow()
    main_window.show()

    sys.exit(app.exec())
    