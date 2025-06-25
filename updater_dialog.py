import os
import ctypes

from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QFont, QIcon

from updater_worker import UpdaterWorker

class UpdaterDialog(QDialog):
    def __init__(self, target_path) -> None:
        super().__init__()
        self.target_path = target_path
        self.setWindowTitle("LegacyPlay Updater")
        self.setFixedSize(500, 220)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        
        title_label = QLabel("LegacyPlay Updater", self)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; padding-bottom: 5px;")
        
        self.label = QLabel("Initializing update process...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("padding: 8px 0;")
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                margin: 10px 0 15px 0;
            }
        """)
        
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.confirm_cancel)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(0)
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.closing_enabled = True

        self.thread = QThread(self)
        self.worker = UpdaterWorker(target_path)
        self.setWindowIcon(QIcon(self.worker.icon_path))
        self.worker.moveToThread(self.thread)
        self.worker.status.connect(self.label.setText)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.status.connect(self.check_status_for_extraction)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def check_status_for_extraction(self, status_text) -> None:
        if "Extracting" in status_text:
            self.set_cancel_visible(False)
        else:
            self.set_cancel_visible(True)

    def set_cancel_visible(self, visible) -> None:
        self.cancel_button.setVisible(visible)
        self.closing_enabled = visible

    def confirm_cancel(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Cancel")
        msg.setText("Are you sure you want to cancel the update process?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        reply = msg.exec()
        if reply == QMessageBox.Yes:
            self.worker.request_stop()
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            self.worker.cleanup()
            self.thread = None
            self.close()

    def on_finished(self, success, message) -> None:
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.set_cancel_visible(True)
        if success:
            self.label.setText(message)
            self.cancel_button.setText("Launching...")
            self.cancel_button.setEnabled(False)
            QTimer.singleShot(2000, self.launch_and_exit)
        else:
            self.cancel_button.setText("Close")
            self.cancel_button.setEnabled(True)
            QMessageBox.critical(self, "Update Failed", message)

    def launch_and_exit(self) -> None:
        launcher_path = os.path.join(self.target_path, "LegacyPlay_Launcher.exe")
        if os.path.exists(launcher_path):
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", launcher_path, None, self.target_path, 1)
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch LegacyPlay: {e}")
        self.close()

    def closeEvent(self, event) -> None:
        if not self.closing_enabled:
            event.ignore()
            return
        if self.thread and self.thread.isRunning():
            self.worker.request_stop()
            self.thread.quit()
            self.thread.wait()
            self.worker.cleanup()
            self.thread = None
        event.accept()