import os
import ctypes

from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QThread, QTimer

from updater_worker import UpdaterWorker

class UpdaterDialog(QDialog):
    def __init__(self, target_path):
        super().__init__()
        self.target_path = target_path
        self.setWindowTitle("LegacyPlay Updater")
        self.setFixedSize(420, 180)
        self.label = QLabel("Initializing updater...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.confirm_cancel)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.closing_enabled = True

        self.thread = QThread(self)
        self.worker = UpdaterWorker(target_path)
        self.worker.moveToThread(self.thread)
        self.worker.status.connect(self.label.setText)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.status.connect(self.check_status_for_extraction)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def check_status_for_extraction(self, status_text):
        if "Extracting" in status_text:
            self.set_cancel_visible(False)
        else:
            self.set_cancel_visible(True)

    def set_cancel_visible(self, visible):
        self.cancel_button.setVisible(visible)
        self.closing_enabled = visible

    def confirm_cancel(self):
        reply = QMessageBox.question(self, "Confirm Cancel", "Are you sure you want to cancel the update process?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.worker.request_stop()
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            self.worker.cleanup()
            self.thread = None
            self.close()

    def on_finished(self, success, message):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.set_cancel_visible(True)
        if success:
            self.label.setText(message)
            QTimer.singleShot(2000, self.launch_and_exit)
        else:
            QMessageBox.critical(self, "Update Failed", message)
            self.close()

    def launch_and_exit(self):
        launcher_path = os.path.join(self.target_path, "LegacyPlay_Launcher.exe")
        if os.path.exists(launcher_path):
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", launcher_path, None, self.target_path, 1)
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch LegacyPlay: {e}")
        self.close()

    def closeEvent(self, event):
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
