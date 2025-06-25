import sys
import os
import subprocess
from typing import Never
from PySide6.QtWidgets import QApplication, QMessageBox
from updater_dialog import UpdaterDialog

STYLE_SHEET = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
}
QDialog {
    background-color: #121212;
    color: #f0f0f0;
}
QLabel {
    color: #ffffff;
    font-size: 14px;
    font-weight: 400;
    padding: 5px 0;
}
QProgressBar {
    border: 1px solid #333;
    border-radius: 8px;
    background-color: #1e1e1e;
    height: 24px;
}
QProgressBar::chunk {
    background-color: #00aaff;
    border-radius: 8px;
}
QPushButton {
    padding: 10px 30px;
    border: none;
    border-radius: 6px;
    background-color: #007acc;
    color: white;
    font-size: 14px;
    font-weight: 500;
    min-width: 150px;
}
QPushButton:hover {
    background-color: #006bb3;
}
QPushButton:pressed {
    background-color: #005c99;
}
QPushButton:disabled {
    background-color: #3a3a3a;
    color: #888;
}
QMessageBox {
    background-color: #121212;
    color: #f0f0f0;
}
QMessageBox QLabel {
    color: #ffffff;
    font-size: 14px;
}
QMessageBox QPushButton {
    background-color: #007acc;
    color: white;
    padding: 8px 20px;
    border-radius: 5px;
    min-width: 100px;
    font-size: 13px;
}
QMessageBox QPushButton:hover {
    background-color: #006bb3;
}
"""

def show_error(parent, title, message) -> None:
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setStyleSheet(STYLE_SHEET)
    msg_box.exec()

def main() -> Never:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE_SHEET)
    
    if len(sys.argv) < 2:
        show_error(None, "Error", "Missing target path argument.")
        sys.exit(1)
    target_path = sys.argv[1]
    if not os.path.isdir(target_path):
        show_error(None, "Error", f"Invalid directory: {target_path}")
        sys.exit(1)
    
    subprocess.Popen(
        ["taskkill", "/F", "/IM", "LegacyPlay_Launcher.exe"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    dialog = UpdaterDialog(target_path)
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()