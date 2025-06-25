import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from updater_dialog import UpdaterDialog

STYLE_SHEET = """
QDialog {
    background-color: #121212;
    color: #f0f0f0;
}
QLabel {
    color: #ffffff;
    font-size: 13px;
}
QProgressBar {
    border: 1px solid #333;
    border-radius: 6px;
    background-color: #1e1e1e;
    height: 14px;
}
QProgressBar::chunk {
    background-color: #00aaff;
    border-radius: 6px;
}
QPushButton {
    padding: 8px 25px;
    border: none;
    border-radius: 5px;
    background-color: #007acc;
    color: white;
    font-size: 13px;
    min-width: 140px;
}
QPushButton:hover {
    background-color: #006bb3;
}
QPushButton:pressed {
    background-color: #005c99;
}
QMessageBox {
    background-color: #121212;
    color: #f0f0f0;
}
QMessageBox QLabel {
    color: #ffffff;
}
QMessageBox QPushButton {
    background-color: #007acc;
    color: white;
    padding: 5px 15px;
    border-radius: 4px;
}
QMessageBox QPushButton:hover {
    background-color: #006bb3;
}
"""

def show_error(parent, title, message):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setStyleSheet(STYLE_SHEET)
    msg_box.exec()

def main():
    app = QApplication(sys.argv)
    if len(sys.argv) < 2:
        show_error(None, "Error", "Missing target path argument.")
        sys.exit(1)
    target_path = sys.argv[1]
    if not os.path.isdir(target_path):
        show_error(None, "Error", f"Invalid directory: {target_path}")
        sys.exit(1)
    dialog = UpdaterDialog(target_path)
    dialog.setStyleSheet(STYLE_SHEET)
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
