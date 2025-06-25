import os
import urllib.request
import urllib.error
import zipfile
import shutil
import hashlib

from PySide6.QtCore import QObject, Signal

class UpdaterWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, target_path):
        super().__init__()
        self.target_path = target_path
        self.stop_requested = False
        self.temp_dir = os.path.join(os.environ.get('TEMP'), 'LP_Upd')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.zip_path = ""

    def run(self):
        try:
            self.status.emit("Fetching version info...")
            version = self.get_online_version()
            if not version:
                raise Exception("Failed to retrieve version info.")
            self.status.emit(f"Preparing update {version}...")
            self.zip_path = os.path.join(self.temp_dir, f'update_{version}.zip')
            self.status.emit("Downloading update...")
            self.download_zip(version)
            if self.stop_requested:
                self.cleanup()
                return
            self.status.emit("Extracting files...")
            self.extract_zip()
            self.cleanup()
            self.finished.emit(True, f"Update {version} completed. Launching...")
        except Exception as e:
            self.cleanup()
            self.finished.emit(False, str(e))

    def get_online_version(self):
        try:
            with urllib.request.urlopen("https://legacyplay.retify.lol/current_ver.txt", timeout=10) as response:
                return response.read().decode('utf-8').strip()
        except:
            return None

    def download_zip(self, version):
        url = f"https://legacyplay.retify.lol/zips/{version}.zip"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                total_size = response.headers.get('Content-Length')
                total_size = int(total_size) if total_size else 0
                downloaded = 0
                block_size = 8192
                with open(self.zip_path, 'wb') as f:
                    while True:
                        if self.stop_requested:
                            return
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = min(int(downloaded * 100 / total_size), 100)
                            self.progress.emit(percent)
                            mb_text = f"Downloading: {downloaded // (1024*1024)} MB / {total_size // (1024*1024)} MB"
                            self.status.emit(mb_text)
                if total_size and downloaded < total_size:
                    raise Exception("Download incomplete.")
                if not total_size:
                    self.progress.emit(100)
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP error: {e.code}")
        except urllib.error.URLError:
            raise Exception("Failed to download update.")

    def extract_zip(self):
        try:
            with zipfile.ZipFile(self.zip_path) as zip_ref:
                files = zip_ref.infolist()
                total_files = len(files)
                for i, file in enumerate(files):
                    if self.stop_requested:
                        return
                    target_file = os.path.join(self.target_path, file.filename)
                    if file.is_dir():
                        os.makedirs(target_file, exist_ok=True)
                        continue
                    extract_needed = True
                    if os.path.exists(target_file):
                        archive_hash = self.compute_md5_zip(zip_ref, file)
                        local_hash = self.compute_md5_file(target_file)
                        if archive_hash == local_hash:
                            extract_needed = False
                    if extract_needed:
                        if os.path.exists(target_file):
                            try:
                                os.remove(target_file)
                            except PermissionError:
                                try:
                                    os.chmod(target_file, 0o777)
                                    os.remove(target_file)
                                except:
                                    pass
                        try:
                            zip_ref.extract(file, self.target_path)
                        except PermissionError:
                            try:
                                os.chmod(target_file, 0o777)
                                os.remove(target_file)
                                zip_ref.extract(file, self.target_path)
                            except:
                                raise Exception(f"Failed to replace locked file: {file.filename}")
                    percent = int((i + 1) * 100 / total_files)
                    self.progress.emit(percent)
                    mb_text = f"Extracting: {i+1} / {total_files} files"
                    self.status.emit(mb_text)
        except zipfile.BadZipFile:
            raise Exception("Downloaded file is not a valid ZIP archive.")
        except PermissionError:
            raise Exception("Access denied while extracting files.")
        except Exception as e:
            raise Exception(f"Failed to extract files: {e}")

    def compute_md5_file(self, path):
        h = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None

    def compute_md5_zip(self, zip_ref, file_info):
        h = hashlib.md5()
        try:
            with zip_ref.open(file_info) as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None

    def cleanup(self):
        try:
            if os.path.exists(self.zip_path):
                os.remove(self.zip_path)
            if os.path.isdir(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

    def request_stop(self):
        self.stop_requested = True