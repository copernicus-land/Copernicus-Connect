import os
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox, QStyle
from PyQt5.QtGui import QIntValidator, QIcon

LIMIT_UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "limit_dialog.ui")

FORM_CLASS, _ = uic.loadUiType(LIMIT_UI_PATH)

CONFIG_PATH = Path.home() / ".hda_limit"

class LimitDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))

        # Setup validator (only allow integers >= 0)
        self.lineEditLimit.setValidator(QIntValidator(0, 999999))

        # Load existing limit or default
        self.lineEditLimit.setText(self.load_saved_limit())

        self.btnSave.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btnCancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))

        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.reject)

    def save(self):
        text = self.lineEditLimit.text().strip()
        if text == "":
            QMessageBox.warning(self, "Input Error", "Please enter a limit (0 or higher).")
            return
        try:
            value = int(text)
            if value < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Only positive integers (including 0) are allowed.")
            return

        with open(CONFIG_PATH, 'w') as f:
            f.write(str(value))

        self.accept()

    def load_saved_limit(self):
        if CONFIG_PATH.is_file():
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return str(int(f.read().strip()))  # ensure it's an integer string
            except ValueError:
                return "0"  # fallback if file content is invalid
        return "0"
