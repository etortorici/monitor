import monitor.main as monitor
from monitor.communication.server import GpibServer
from threading import Thread
import sys
import argparse
from PySide6.QtWidgets import QApplication


def lakeshore():
    """Launch Server"""
    parser = argparse.ArgumentParser(
        prog="lakeshore",
        description="Launch monitoring program for LakeShore",
        epilog="author: Teddy Tortorici <edward.tortorici@colorado.edu>"
    )
    parser.add_argument("model_number", type=int, default=340,
                        help="What is the model number for the LakeShore (331 or 340)?")
    args = parser.parse_args()
    server = GpibServer(None, args.model_number)
    server_thread = Thread(target=server.run, args=())
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)

    main_window = monitor.MainWindow()
    main_window.show()

    sys.exit(app.exec())
    
