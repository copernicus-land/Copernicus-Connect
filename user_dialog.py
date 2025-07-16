import os
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QStyle, QLineEdit
)

USER_UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "user_dialog.ui")
FORM_CLASS, _ = uic.loadUiType(USER_UI_PATH)

class UserDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

      
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))

        self.btnSave.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btnCancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))

        self.lineEditPassword.setEchoMode(QLineEdit.Password)

 
        self.lineEditUsername.setToolTip("Enter your WEkEO username")
        self.lineEditPassword.setToolTip("Enter your WEkEO password")

        self.btnSave.clicked.connect(self.save_credentials)
        self.btnCancel.clicked.connect(self.reject)

        self.load_credentials()

    def load_credentials(self):
        hdarc = Path.home() / ".hdarc"
        if hdarc.exists():
            try:
                with open(hdarc, 'r') as f:
                    lines = f.readlines()
                creds = {
                    key.strip(): val.strip()
                    for line in lines if ":" in line
                    for key, val in [line.strip().split(":", 1)]
                }
                self.lineEditUsername.setText(creds.get("user", ""))
                self.lineEditPassword.setText(creds.get("password", ""))
            except Exception as e:
                print(f"⚠️ Error reading .hdarc: {e}")

    def save_credentials(self):
        username = self.lineEditUsername.text().strip()
        password = self.lineEditPassword.text().strip()

        if username and password:
            hdarc = Path.home() / ".hdarc"
            try:
                with open(hdarc, 'w') as f:
                    f.write(f"user:{username}\n")
                    f.write(f"password:{password}\n")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save credentials:\n{e}")
        else:
            QMessageBox.warning(self, "Missing Input", "Please enter both username and password.")

            
