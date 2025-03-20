import monitor.main as monitor
from monitor.communication.server import GpibServer
from threading import Thread
import sys
from PySide6.QtWidgets import QApplication


def lakeshore():
    """Launch Server"""
    server = GpibServer(None, int(340))
    server_thread = Thread(target=server.run, args=())
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)

    main_window = monitor.MainWindow()
    main_window.show()

    sys.exit(app.exec())
    
