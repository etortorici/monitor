from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Slot


class TextStream(QTextEdit):
    def __init__(self, font: QFont):
        super(self.__class__, self).__init__()
        self.setReadOnly(True)
        self.setFont(font)
        self.setStyleSheet("background-color: rgb(43, 43, 32);"
                           "color: rgb(255, 255, 255);")

    @Slot(str)
    def write(self, text: str):
        """Writes to GUI from the write_thread object attribute"""
        self.moveCursor(QTextCursor.End)
        self.insertHtml(text.replace("\n", "<br>").replace(" ", "&nbsp;"))

        # make the scroll bar scroll with the new text as it fills past the size of the window
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("Test")

    w = TextStream(QFont("Arial", 12))

    window = QMainWindow()
    window.setCentralWidget(w)
    window.show()

    w.write("lskjdf<sub>ljk</sub>\n")
    w.write("lskjdf<sub>ljk</sub>")
    w.write("lskjdf<sub>ljk</sub>")
    app.exec()
