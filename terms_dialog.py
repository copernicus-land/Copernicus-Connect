from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton,
    QMessageBox, QDialogButtonBox, QWidget, QTextBrowser, QHBoxLayout, QStyle
)
from PyQt5 import uic
import os
import requests

TERMS_UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "terms.ui")
FORM_CLASS, _ = uic.loadUiType(TERMS_UI_PATH)

class TermsDialog(QDialog, FORM_CLASS):
    def __init__(self, client, accept_term_id = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.client = client
        self.term_widgets = {}  # term_id -> (checkbox, abstract)
        self.original_accepts = set()
        self.accept_term_id = accept_term_id

        self.load_terms()
        self.load_accepted()

        # Connect save/cancel
        self.buttonBox.accepted.connect(self.save_accepts)
        self.buttonBox.rejected.connect(self.reject)

        save_button = self.buttonBox.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))

        cancel_button = self.buttonBox.button(QDialogButtonBox.Cancel)
        if cancel_button:
            cancel_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))

    def load_terms(self):
        response = self.client.get("terms?startIndex=0&itemsPerPage=20")
        layout = self.scrollWidget.layout()

        # ➕ Tilføj introduktionstekst øverst (én gang)
        intro_label = QLabel("✔ Check the box to accept the terms and conditions")
        intro_label.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(intro_label)

        for feature in response.get("features", []):
            term_id = feature["term_id"]
            title = feature.get("title", "")
            abstract = feature.get("abstract", "")

            checkbox = QCheckBox(title)
            
            if term_id == self.accept_term_id:
                checkbox.setStyleSheet("font-weight: bold;") 
            checkbox.setToolTip("Check to accept this term and condition")

            # Gem abstract for visning
            show_button = QPushButton("Terms and conditions")
            icon = self.style().standardIcon(QStyle.SP_FileIcon)
            show_button.setIcon(icon)
            show_button.clicked.connect(lambda _, text=abstract: self.show_abstract(text))

            # Horisontal layout: checkbox + spacer + knap
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.addWidget(checkbox)
            row_layout.addStretch()
            row_layout.addWidget(show_button)

            layout.addWidget(row)
            self.term_widgets[term_id] = (checkbox, abstract)


    def load_accepted(self):
        response = self.client.get("termsaccepted?startIndex=0&itemsPerPage=20")
        for feature in response.get("features", []):
            term_id = feature["term_id"]
            if feature.get("accepted") and term_id in self.term_widgets:
                checkbox, _ = self.term_widgets[term_id]
                checkbox.setChecked(True)
                checkbox.setStyleSheet("color: green; font-weight: bold;")
                self.original_accepts.add(term_id)

    def save_accepts(self):
        new_accepts = {term_id for term_id, (cb, _) in self.term_widgets.items() if cb.isChecked()}
        to_add = new_accepts - self.original_accepts
        to_remove = self.original_accepts - new_accepts

        for term_id in to_add:
            try:
                self.client.put({}, "termsaccepted", term_id)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to accept: {term_id}\n{e}")

        for term_id in to_remove:
            try:
                url = f"https://gateway.prod.wekeo2.eu/hda-broker/api/v1/termsaccepted/{term_id}"
                headers = {
                    "Authorization": f"Bearer {self.client.token}",
                    "accept": "application/json"
                }

                response = requests.delete(url, headers=headers)
                response.raise_for_status()  

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to unaccept: {term_id}\n{e}")

        self.accept()

    def show_abstract(self, text):
        dialog = QDialog(self)
        dialog.setWindowTitle("Term Abstract")
        layout = QVBoxLayout(dialog)

        viewer = QTextBrowser()
        viewer.setHtml(text) 
        viewer.setMinimumSize(500, 300) 
        layout.addWidget(viewer)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()
