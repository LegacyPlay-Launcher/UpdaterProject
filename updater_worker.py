from urllib.request import _UrlopenRet


import os
import urllib.request
import urllib.error
import zipfile
import shutil
import hashlib
import base64

from PySide6.QtCore import QObject, Signal

class UpdaterWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)

    PRESERVE_FOLDERS = {"Data", "CustomAssets", "CachingFolder"} # we don't want our data wiped :(

    def __init__(self, target_path) -> None:
        super().__init__()
        self.target_path = target_path
        self.stop_requested = False
        self.temp_dir = os.path.join(os.environ.get('TEMP'), 'LP_Upd')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.zip_path = ""
        self.icon_path = os.path.join(self.temp_dir, "LP_UpdaterLogo.ico")
        self.generate_icon()

    def generate_icon(self) -> None:
        base64_icon = "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"
        try:
            icon_data = base64.b64decode(base64_icon)
            with open(self.icon_path, 'wb') as icon_file:
                icon_file.write(icon_data)
        except Exception:
            pass

    def run(self) -> None:
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

    def get_online_version(self) -> _UrlopenRet | None:
        try:
            with urllib.request.urlopen("https://legacyplay.retify.lol/current_ver.txt", timeout=10) as response:
                return response.read().decode('utf-8').strip()
        except:
            return None

    def download_zip(self, version) -> None:
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

    def extract_zip(self) -> None:
        try:
            expected_paths = set()
            with zipfile.ZipFile(self.zip_path) as zip_ref:
                files = zip_ref.infolist()
                total_files = len(files)
                for i, file in enumerate(files):
                    if self.stop_requested:
                        return
                    path = file.filename
                    if path.endswith('/'):
                        path = path.rstrip('/')
                    if path:
                        parts = path.split('/')
                        expected_paths.add(path)
                        for idx in range(1, len(parts)):
                            parent_path = '/'.join(parts[:idx])
                            expected_paths.add(parent_path)
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
                self.status.emit("Cleaning up old files and directories...")
                self.cleanup_old_files(expected_paths)
        except zipfile.BadZipFile:
            raise Exception("Downloaded file is not a valid ZIP archive.")
        except PermissionError:
            raise Exception("Access denied while extracting files.")
        except Exception as e:
            raise Exception(f"Failed to extract files: {e}")

    def cleanup_old_files(self, expected_paths) -> None:
        for root, dirs, files in os.walk(self.target_path, topdown=False):
            if self.stop_requested:
                return
            for name in files:
                if self.stop_requested:
                    return
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, self.target_path).replace('\\', '/')
                if rel_path in expected_paths:
                    continue
                if any(rel_path.startswith(folder + '/') for folder in self.PRESERVE_FOLDERS):
                    continue
                try:
                    os.remove(full_path)
                except Exception:
                    pass
            for name in dirs:
                if self.stop_requested:
                    return
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, self.target_path).replace('\\', '/')
                if rel_path in expected_paths:
                    continue
                if any(rel_path.startswith(folder + '/') or rel_path == folder for folder in self.PRESERVE_FOLDERS):
                    continue
                try:
                    shutil.rmtree(full_path, ignore_errors=True)
                except Exception:
                    pass

    def compute_md5_file(self, path) -> str | None:
        h = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None

    def compute_md5_zip(self, zip_ref, file_info) -> str | None:
        h = hashlib.md5()
        try:
            with zip_ref.open(file_info) as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None

    def cleanup(self) -> None:
        try:
            if os.path.exists(self.zip_path):
                os.remove(self.zip_path)
            if os.path.isdir(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

    def request_stop(self) -> None:
        self.stop_requested = True