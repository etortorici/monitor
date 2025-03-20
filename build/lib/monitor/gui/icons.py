import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle, QWidget


def built_in(parent: QWidget, icon_name: str) -> QIcon:
    return QIcon(parent.style().standardIcon(getattr(QStyle, f'SP_{icon_name}')))


def custom(icon_name: str) -> QIcon:
    return QIcon(os.path.join('gui', 'custom_icons', icon_name))
