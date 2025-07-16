import os
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QFileDialog, QStyle
from PyQt5.QtGui import QIcon

PATH_UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "path_dialog.ui")

FORM_CLASS, _ = uic.loadUiType(PATH_UI_PATH)

DEFAULT_DOWNLOAD_PATH = str(Path.home() / "HDA_Downloads")
CONFIG_PATH = Path.home() / ".hda_path"

class PathDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))

        # Load saved path or default
        self.lineEditPath.setText(self.load_saved_path())

        self.btnBrowse.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.btnSave.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btnCancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))

        self.btnBrowse.clicked.connect(self.browse)
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.reject)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select download folder")
        if folder:
            self.lineEditPath.setText(folder)

    def save(self):
        path = self.lineEditPath.text().strip()
        if not path:
            path = DEFAULT_DOWNLOAD_PATH

        with open(CONFIG_PATH, 'w') as f:
            f.write(path)

        self.accept()

    def load_saved_path(self):
        if CONFIG_PATH.is_file():
            with open(CONFIG_PATH, 'r') as f:
                return f.read().strip()
        return DEFAULT_DOWNLOAD_PATH
