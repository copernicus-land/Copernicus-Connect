try:
    from qgis.core import QgsMessageLog, Qgis, QgsRasterLayer, QgsProject
    from qgis.utils import iface
    from .user_dialog import UserDialog
    from .path_dialog import PathDialog
    from .limit_dialog import LimitDialog
    from .widgets.bbox_widget import BoundingBoxWidget
    from .get_wms import WMSCapabilitiesParser
    from .get_wmts import WMTSCapabilitiesParser
    from  .get_base_url import GetBaseURL
    from .terms_dialog import TermsDialog
    from .loading_overlay import LoadingOverlay
    running_in_qgis = True
    def log_message(msg, tag="Copernicus Connect", level="INFO"):
        level_str = level.upper() if isinstance(level, str) else "INFO"
        qgis_level = {
            "INFO": Qgis.Info,
            "WARNING": Qgis.Warning,
            "ERROR": Qgis.Critical,
            "SUCCESS": Qgis.Success,
        }.get(level_str, Qgis.Info)
        QgsMessageLog.logMessage(str(msg), tag, qgis_level)
except ImportError as e:    
    from user_dialog import UserDialog
    from path_dialog import PathDialog
    from limit_dialog import LimitDialog
    from widgets.bbox_widget import BoundingBoxWidget
    from get_wms import WMSCapabilitiesParser
    from get_wmts import WMTSCapabilitiesParser
    from  get_base_url import GetBaseURL
    from terms_dialog import TermsDialog
    from loading_overlay import LoadingOverlay
    running_in_qgis = False
    
    def log_message(msg, tag="Copernicus Connect", level="INFO"):
        print(f"[{level}] {tag}: {msg}")
        QgsVectorLayer = None
        QgsProject = None
    

import sys
import os
import json
import requests
import time
import webbrowser
import platform
import subprocess
from pathlib import Path
from urllib.parse import urlencode
from collections import defaultdict
from io import BytesIO
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QDateTimeEdit, QStyle, QVBoxLayout, QTextEdit, QPushButton, QDialogButtonBox, 
    QLineEdit, QLabel, QDialog, QMessageBox, QListWidget, QListWidgetItem, QDockWidget, QToolButton, QHBoxLayout, QWidget
)
from PyQt5.QtCore import (QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QDateTime, Qt, QStringListModel, QModelIndex, QTimer)
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QIcon, QPixmap, QClipboard
from hda import Client, Configuration


UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "form.ui")
base_path = os.path.dirname(os.path.abspath(__file__))
json_path_dataset = os.path.join(base_path, "resources", "dataset.json")
image_placeholder = os.path.join(base_path, "resources", "placeholder.png")




def format_size(size_bytes):
    if size_bytes >= 1024 ** 3:
        size_gb = size_bytes / (1024 ** 3)
        size_str = f"{size_gb:.2f} GB"
    else:
        size_mb = size_bytes / (1024 ** 2)
        size_str = f"{size_mb:.1f} MB"
    
    return size_str

def get_saved_limit(default=0): 
        limitfile = Path.home() / ".hda_limit"
        if limitfile.is_file():
            try:
                value = int(limitfile.read_text().strip())
                if value >= 0:
                    return value
            except ValueError:
                pass
        return default

def build_field_definitions(queryable_dict):
    properties = queryable_dict.get("properties", {})
    required = queryable_dict.get("required", [])
    fields = []

    for key, prop in properties.items():
        field = {
            "name": key,
            "label": prop.get("title", key),
            "type": prop.get("type", "string"),
            "required": key in required,
            "choices": None,
            "format": prop.get("format"),
            "pattern": prop.get("pattern"),
        }
        
        if "oneOf" in prop:
            field["choices"] = prop["oneOf"]  
        elif "items" in prop and isinstance(prop["items"], dict) and "oneOf" in prop["items"]:
            field["choices"] = prop["items"]["oneOf"]

        fields.append(field)

    return fields

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QToolButton, QDialog,
    QDialogButtonBox, QVBoxLayout, QHBoxLayout, QDateTimeEdit
)

class NullableDateTimeInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line = QLineEdit(self)
        self.line.setPlaceholderText("Click the 📅 to pick a date…")

        btn = QToolButton(self)
        btn.setText("📅")
        btn.clicked.connect(self.open_picker)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line)
        layout.addWidget(btn)

    def open_picker(self):
        # 1) Create a small dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Select Date and Time")
        vlayout = QVBoxLayout(dlg)

        # 2) Add a QDateTimeEdit to the dialog
        dtedit = QDateTimeEdit(dlg)
        dtedit.setCalendarPopup(True)
        dtedit.setDisplayFormat("yyyy-MM-ddTHH:mm:ss")

        # Initialize with current value or today’s date if blank
        current_text = self.line.text().strip()
        current_dt = QDateTime.fromString(current_text, "yyyy-MM-ddTHH:mm:ss")
        if current_dt.isValid():
            dtedit.setDateTime(current_dt)
        else:
            # Show today's date/time by default
            dtedit.setDateTime(QDateTime.currentDateTime())

        vlayout.addWidget(dtedit)

        # 3) OK / Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=dlg
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        vlayout.addWidget(buttons)

        # 4) Run the dialog
        if dlg.exec_() == QDialog.Accepted:
            chosen = dtedit.dateTime()
            self.line.setText(chosen.toString("yyyy-MM-ddTHH:mm:ss"))
        # If Cancel, do nothing — leave the field as it was

    def clear(self):
        """Completely clear the field."""
        self.line.clear()

    def get_nullable(self):
        """Return None or an ISO timestamp string."""
        txt = self.line.text().strip()
        if not txt:
            return None
        dt = QDateTime.fromString(txt, "yyyy-MM-ddTHH:mm:ss")
        return None if not dt.isValid() else txt


class DownloadWorkerSignals(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

class DownloadWorker(QRunnable):
    def __init__(self, matches, client, query, selected_ids, out_dir):
        super().__init__()
        self.matches = matches
        self.client = client
        self.query = query
        self.selected_ids = selected_ids
        self.out_dir = out_dir
        self.cancelled = False
        self.signals = DownloadWorkerSignals()
        
    def cancel(self):
        self.cancelled = True

    @pyqtSlot()
    def run(self):
        try:
            downloaded = 0
            total = len(self.selected_ids)
            futures = []

            with ThreadPoolExecutor(max_workers=4) as executor:
                for match in self.matches:
                    if self.cancelled:
                        self.signals.status.emit("Download cancelled.")
                        return
                    feature_id = match.results[0]['id']
                    if feature_id in self.selected_ids:
                        self.signals.status.emit(f"Downloading {feature_id}...")
                        futures.append(
                            executor.submit(self.download_file, match)
                        )
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        downloaded += 1
                        progress = int((downloaded / total) * 100)
                        self.signals.progress.emit(progress)
                    except Exception as e:
                        tb = traceback.format_exc()
                        self.signals.error.emit(f"Error during download: {e}\n\n{tb}")

            self.signals.status.emit("Download finished.")
            self.signals.finished.emit()

        except Exception as e:
            tb = traceback.format_exc()
            self.signals.error.emit(f"Unexpected error: {e}\n\n{tb}")

    def download_file(self, match):
        url = match.get_download_urls()[0]
        file_id = match.results[0]['id']
        destination_path = os.path.join(str(self.out_dir), f"{file_id}.zip")
        headers = {"Authorization": f"Bearer {self.client.token}"}

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                if self.cancelled:
                    self.signals.status.emit("Download cancelled.")
                    return
              
                if os.path.exists(destination_path):
                    os.remove(destination_path)

                response = requests.get(url, headers=headers, stream=True, timeout=60)

                if response.status_code == 200:
                    with open(destination_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.cancelled:
                                self.signals.status.emit("Download cancelled during file write.")
                                return
                            if chunk:
                                f.write(chunk)

                    log_message(f"[THREAD] Download OK for {file_id} (attempt {attempt})", "Copernicus Connect", "SUCCESS")
                    return 

                else:
                    log_message(f"[THREAD] Attempt {attempt} failed for {file_id} with status code: {response.status_code}", "Copernicus Connect", "ERROR")

            except Exception as e:
                log_message(f"[THREAD] Attempt {attempt} ERROR for {file_id}: {e}", "Copernicus Connect", "CRITICAL")

            
            time.sleep(5)  

        log_message(f"[THREAD] All attempts failed for {file_id}", "Copernicus Connect", "CRITICAL")


class UiForm(QMainWindow):
    def __init__(self, client):
        super().__init__()
        uic.loadUi(UI_PATH, self)

        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Copernicus Connect")

        self.loadingOverlay = LoadingOverlay(self.tabWidget) 

        if hasattr(self, "splitterQueryForm"):
            self.splitterQueryForm.setStretchFactor(1, 3)  # scrollArea
            self.splitterQueryForm.setStretchFactor(1, 1)  # controls below

     
        if hasattr(self, "splitterWMS"):
            self.splitterWMS.setStretchFactor(0, 3)  # treeViewWMS
            self.splitterWMS.setStretchFactor(1, 1)  # txt_info


        self.client = client
        self.fields = []
        self.widgets = {}
        self.dataset_metadata = {}
        self.matches = []
        self.layer_data = []
        self.wms_layers = {}  
        self.model = QStringListModel()
        self.treeViewWMS.setModel(self.model)

        self.centralwidget.layout().setContentsMargins(10, 10, 10, 10)

        self.load_datasetsButton.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.viewQueryButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.showRequestButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.requestDataButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        self.selectAllButton.setIcon(QIcon(self.resource_path("icon", "select_all.ico")))
        self.clearAllButton.setIcon(QIcon(self.resource_path("icon", "clear_all.ico")))
        self.btn_open_file_location.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btn_download_location.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.downloadButton.setIcon(QIcon( self.resource_path("icon", "product_download.png")))
        self.cancelButton.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.addToLayersButton.setIcon(QIcon(self.resource_path("icon", "layer_add.ico")))

        self.tabWidget.setTabIcon(0,QIcon( self.resource_path("icon", "product_download.png")))
        self.tabWidget.setTabIcon(1,QIcon( self.resource_path("icon", "wms.png")))
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        # Connect buttons and actions
        self.actionUser.triggered.connect(self.show_user_settings)
        self.actionPaths.triggered.connect(self.show_path_settings)
        self.actionLimit.triggered.connect(self.open_limit_dialog)
        self.actionTerms.triggered.connect(self.open_terms_dialog)
        self.load_datasetsButton.clicked.connect(self.load_datasets)
        self.txtFilter.returnPressed.connect(self.load_datasets)
        self.datasetComboBox.currentIndexChanged.connect(self.update_dataset_details)
        self.dataCatalogButton.clicked.connect(self.open_data_catalog)
        self.dataCatalogButton.setEnabled(False)
        self.showRequestButton.clicked.connect(self.show_request)
        self.requestDataButton.clicked.connect(self.request_data)
        self.viewQueryButton.clicked.connect(self.show_query_parameters)
        self.downloadButton.clicked.connect(self.download_selected_files)
        self.selectAllButton.clicked.connect(self.select_all_items)
        self.clearAllButton.clicked.connect(self.clear_selection)
        self.btn_download_location.clicked.connect(self.show_path_settings)
        self.btn_open_file_location.clicked.connect(self.open_file_location)
        self.cancelButton.clicked.connect(self.cancel_download)

        self.limitLineEdit.setValidator(QIntValidator(0, 999999))

        if hasattr(self, 'txtSearchWMS'):
            self.txtSearchWMS.textChanged.connect(lambda text: self.search_in_treeview(self.treeViewWMS, text))

        self.limitLineEdit.setText(str(get_saved_limit()))
        self.formLayout = self.scrollWidget.layout()
        self.addToLayersButton.clicked.connect(self.handle_add_to_layers)
        self.treeViewWMS.doubleClicked.connect(self.handle_add_to_layers)

   
    def resource_path(self, *paths):
        return os.path.join(base_path, "resources", *paths)

    def open_data_catalog(self):
        dataset_id = self.datasetComboBox.currentData()
        try:
            with open(json_path_dataset, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data:
                if entry.get("dataset_id") == dataset_id:
                    catalog_url = entry.get("catalog_url")
                    if catalog_url:
                        webbrowser.open(catalog_url)
                        return
            QMessageBox.information(self, "Data Catalog", "Could not find Data Catalog for selected dataset.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"Could not find file: {json_path_dataset}")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"JSON decode error: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def open_terms_dialog(self, term_id = None):
        try:
            dialog = TermsDialog(self.client, term_id, self)
            if dialog.exec_():
                print("Terms saved.")
            else:
                print("Cancelled.")
        except Exception as e:
            print(e)

    def open_file_location(self):
        folder_path = self.get_download_path()
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Invalid Path", f"The folder does not exist:\n{folder_path}")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder:\n{folder_path}\n\n{str(e)}")


    def get_dataset_info(self, dataset_id):
        try:
            with open(json_path_dataset, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data:
                if entry.get("dataset_id") == dataset_id:
                    return entry
            get_base_url = GetBaseURL()
            entry = get_base_url.get_layer_data(dataset_id)
            if entry is not None:
                return entry
        except FileNotFoundError:
            print(f"❌ File '{json_path_dataset}' not found.")
        except json.JSONDecodeError as e:
            print(f"❌ JSON error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        model = None
        self.treeViewWMS.setModel(model)
        return None
    
    def on_tab_changed(self, index):
        if index == 1:
            selected_id = self.datasetComboBox.currentData()
            if not selected_id:
                self.datasetDetails.clear()
                return

            self.loadingOverlay.show("🔄 Loading wms/wmts")
            QApplication.processEvents()

            get_capability = self.dataset_metadata.get(selected_id, {}).get("get_capability", None)
            self.load_layer_data(selected_id, get_capability)

            self.loadingOverlay.hide()

    def populate_treeview(self, treeview, layers):
        grouped = defaultdict(list)
        for layer in layers:
            raw_name = layer.get("name", "")
            group_name = raw_name.split("/")[1] if "/" in raw_name else (raw_name or "Uden navn")
            grouped[group_name].append(layer)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Layers to open in QGIS"])  

        for group_name, layer_list in sorted(grouped.items(), key=lambda x: x[0].lower()):
            parent_item = QStandardItem(group_name)
            parent_item.setFlags(Qt.ItemIsEnabled)  # ikke selv klikbar

            for layer in sorted(layer_list, key=lambda x: x.get("title", "").lower()):
                title = layer.get("title", "Uden titel")
                child_item = QStandardItem(title)
                child_item.setData(layer, role=Qt.UserRole)
                parent_item.appendRow(child_item)

            model.appendRow(parent_item)

        treeview.setModel(model)
        treeview.selectionModel().currentChanged.connect(self.on_treeview_selection_changed)

        treeview.setHeaderHidden(True)
        treeview.collapseAll()
        treeview.setEditTriggers(treeview.NoEditTriggers)

    

    def search_in_treeview(self, treeview, search_text):
        model = treeview.model()
        if not model:
            return

        treeview.clearSelection()
        search_text = search_text.strip().lower()
        found_indexes = []

        for group_row in range(model.rowCount()):
            group_item = model.item(group_row)
            group_visible = False  # flag for at vise/skjule hele gruppen

            # Gennemgå child-items (lag)
            for child_row in range(group_item.rowCount()):
                child_item = group_item.child(child_row)
                label = child_item.text()

                # Nulstil font
                font = child_item.font()
                font.setBold(False)
                child_item.setFont(font)

                if search_text in label.lower():
                    # Match fundet
                    group_visible = True
                    font.setBold(True)
                    child_item.setFont(font)
                    index = child_item.index()
                    found_indexes.append(index)

            treeview.setRowHidden(group_row, QModelIndex(), not group_visible)

        if found_indexes:
            treeview.setCurrentIndex(found_indexes[0])
            treeview.scrollTo(found_indexes[0])


    def on_treeview_selection_changed(self, current, previous):
        item = current.model().itemFromIndex(current)
        layer = item.data(Qt.UserRole)

        if not layer:
            self.txt_info.clear()
            return

        info = [
            "🧪 Selected Layer:",
            f"Name: {layer.get('name', '')}",
            f"Title: {layer.get('title', '')}",
            f"QGIS URI: {layer.get('qgis_uri', '')}"
        ]
        self.txt_info.setPlainText("\n".join(info))

    def load_layer_data(self, dataset_id, get_capability = None):
        dataset_info = self.get_dataset_info(dataset_id)
        if dataset_info:
            urls = dataset_info["capabilities_url"]
            layer_type = dataset_info.get("type", "wms")
            all_layers = []
            for url in urls:
                try:
                    if layer_type == 'wms':
                        parser = WMSCapabilitiesParser(url)
                    elif layer_type == 'wmts':
                        parser = WMTSCapabilitiesParser(url)
                    else:
                        print(f"❌ Unknown layer type: {layer_type} for URL: {url}")
                        continue
                    service = parser.get_service_metadata()
                    layers = parser.get_layers()
                    all_layers.extend(layers)
                except Exception as e:
                    print(f"❌ Error parsing {url}: {e}")
            self.populate_treeview(self.treeViewWMS, all_layers)
            self.txt_info.clear()

    def show_temporal_panel(self):
        """Try to show the default Temporal Panel dock widget."""
        for dock in iface.mainWindow().findChildren(QDockWidget):
            if dock.objectName() == "Temporal Controller":
                dock.setVisible(True)
                return True
        return False

    def handle_add_to_layers(self):
        try:
            index = self.treeViewWMS.currentIndex()
            if not index.isValid():
                QMessageBox.warning(self, "No Selection", "No layer selected. Please select a specific layer from the list.")
                return

            model = self.treeViewWMS.model()
            item = model.itemFromIndex(index)
            layer_data = item.data(Qt.UserRole)

            if not layer_data:
                QMessageBox.warning(self, "Invalid Selection", "Selected item is a group. Please select a specific layer.")
                return

            qgis_uri = layer_data.get('qgis_uri')
            layer_type = layer_data.get('type', 'wms')
            title = layer_data.get('title', layer_data.get('name'))

            QgsMessageLog.logMessage(f"Adding layer: {title}", "Corpernicus Connect", Qgis.Info)
            QgsMessageLog.logMessage(f"URI: {qgis_uri}", "Corpernicus Connect", Qgis.Info)
            QgsMessageLog.logMessage(f"Type: {layer_type}", "Corpernicus Connect", Qgis.Info)

            qgs_layer = QgsRasterLayer(qgis_uri, title, layer_type)

            if not qgs_layer.isValid():
                QMessageBox.critical(self, "Layer Error", "Failed to create layer. The URI might be incorrect.")
                return

            QgsProject.instance().addMapLayer(qgs_layer)
            QgsMessageLog.logMessage("🎉 Layer successfully added to QGIS.", "Corpernicus Connect", Qgis.Success)

            # Check if layer supports temporal data
            temporal_props = qgs_layer.temporalProperties()
            if temporal_props.isActive():
                QMessageBox.information(self, "Temporal Layer",
                                        f"The layer '{title}' supports temporal data.\n\nThe Temporal Panel will be opened.")
                if not self.show_temporal_panel():
                     QMessageBox.warning(self, "Warning", "Could not open the Temporal Panel (action not found).")
            else:
                QgsMessageLog.logMessage(f"Layer '{title}' is not temporal.", "Corpernicus Connect", Qgis.Info)

        except Exception as e:
            #QgsMessageLog.logMessage(f"❌ Unexpected error: {e}", "Corpernicus Connect", Qgis.Critical)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n\n{e}")


    def add_layer_qgis(self, uri, layers_str, source_type):
        if running_in_qgis:
            layer = QgsRasterLayer(uri, layers_str, "wms")
            print(type(layer))
            print(layer)
            print(uri)

            if layer:
                QgsProject.instance().addMapLayer(layer)
                print(f"✅ Layer added to QGIS: {layers_str}")
                QMessageBox.information(
                    None,
                    "Layer added",
                    f"The layer '{layers_str}' was successfully added to QGIS.\nSource: {source_type}"
                )
            else:
                msg = "❌ The layer is invalid or could not be added."
                print(msg)
                QMessageBox.critical(None, "Layer addition failed", f"{msg}\n\nURI:\n{uri}")

        else:
            print("🧪 Simulering uden QGIS:")
            print(f"Navn: {layers_str}")
            print(f"URI: {uri}")
            
    
        return

    
    def select_all_items(self):
        self.fileListWidget.selectAll()

    def clear_selection(self):
        self.fileListWidget.clearSelection()

    def cancel_download(self):
        if hasattr(self, "worker") and self.worker:
            self.worker.cancel()
            self.statusLabel.setText("Status: Cancelling...")
            self.cancelButton.setEnabled(False)

    def download_finished(self):
        if self.worker.cancelled:
            self.statusLabel.setText("Status: Download cancelled.")
            QMessageBox.information(self, "Cancelled", "Download was cancelled.")
        else:
            self.statusLabel.setText("Status: Download complete.")
            QMessageBox.information(self, "Download complete", "All selected files were downloaded.")

        self.cancelButton.setEnabled(True)
        self.worker = None  

    def insert_thumbnail(self, url):
        pixmap = QPixmap()
        if url is None:
            pixmap.load(image_placeholder)  
        else:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    pixmap.loadFromData(response.content)
                else:
                    pixmap.load(image_placeholder)
            except Exception as e:
                pixmap.load(image_placeholder)  

        self.imageLabel.setPixmap(pixmap)


    def update_dataset_details(self):
        selected_id = self.datasetComboBox.currentData()
        if not selected_id:
            self.datasetDetails.clear()
            return
        
        count = self.datasetComboBox.count()
        number = int(self.datasetComboBox.currentIndex()) + 1

        count_text = f"Number {number} of {count}"
        self.labelCount.setText(count_text)
        
        url = self.dataset_metadata.get(selected_id, {}).get("thumbnail", None)
    
        self.insert_thumbnail(url)

        if self.tabWidget.currentIndex() == 1:
            self.loadingOverlay.show("🔄 Loading wms/wmts")
            QApplication.processEvents()

            get_capability = self.dataset_metadata.get(selected_id, {}).get("get_capability", None)
            self.load_layer_data(selected_id, get_capability)

        abstract = self.dataset_metadata.get(selected_id, {}).get("abstract", "No description available.")
        self.datasetDetails.setPlainText(abstract)
        self.clear_old_widgets()
        self.fileListWidget.clear()
        self.txt_info.clear()
        self.progressBar.setValue(0)
        self.statusLabel.setText("Status: Ready")
  
        self.loadingOverlay.hide()

    def clear_old_widgets(self):
        for i in reversed(range(self.formLayout.count())):
            widget = self.formLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def load_datasets(self):
        

        self.loadingOverlay.show("🔄 Loading datasets...")
        self.loadingOverlay.raise_()
        QTimer.singleShot(0, self.loadingOverlay.repaint)
        QApplication.processEvents()        
        filter_text = self.txtFilter.text().strip()
        params = {"startIndex": 0, "itemsPerPage": 2000}

        if filter_text:
            params["q"] = filter_text

        query_string = urlencode(params)

        try:            
            response = self.client.get(f"datasets?{query_string}")
        except Exception as e:
            print(f"Initial dataset load failed: {e}")
            self.loadingOverlay.hide()

            if not get_user_credentials(self):
                QMessageBox.warning(self, "Login Failed", "Cannot load datasets without valid credentials.")
                return

            username, password = read_credentials()
            conf = Configuration(user=username, password=password)
            self.client = Client(config=conf)
            #self.client.timeout = 10

            try:
                response = self.client.get(f"datasets?{query_string}")
            except Exception as e2:
                print(f"Second dataset load failed: {e2}")
                self.loadingOverlay.hide()
                QMessageBox.critical(self, "Error", "Unable to load datasets. Please check your login.")
                return

        self.datasets = []

        if isinstance(response, list):
            self.datasets = response
        elif "features" in response:
            self.datasets = response["features"]
        elif "content" in response:
            self.datasets = response["content"]

        self.datasetComboBox.clear()
        self.fileListWidget.clear()
        self.datasetComboBox.setEditable(True)
        self.dataset_metadata.clear()
        self.matches.clear()
        self.model.setStringList([]) 
        self.treeViewWMS.setModel(self.model) 
        self.txt_info.clear()

        items = []
        for ds in self.datasets:
            dataset_id = ds.get("dataset_id")
            terms = ds.get("terms", [])
            source = ds.get("metadata", {}).get("_source", {})

            title = source.get("datasetTitle") or dataset_id
            abstract = source.get("abstract", "No description available.")
            temp_begin = source.get("tempextent_begin")
            temp_end = source.get("tempextent_end")
            thumbnail = source.get("thumbnails")           
                    
            # --- Find GetCapabilities-URL from dataset (Not used yet) ---
            get_capability = None
            for dt in source.get("digitalTransfers", []):
                avail = dt.get("availability")
                
                if isinstance(avail, list):
                    for item in avail:
                        url = item.get("url")
                        if url and "GetCapabilities" in url:
                            get_capability = url
                            break
                
                elif isinstance(avail, dict):
                    url = avail.get("url")
                    if url and "GetCapabilities" in url:
                        get_capability = url
                if get_capability:
                    break                
            # ---------------------------------------

            if dataset_id:
                    items.append((title, dataset_id, {
                        "abstract": abstract,
                        "terms": terms,
                        "tempextent_begin": temp_begin,
                        "tempextent_end": temp_end,
                        "thumbnail": thumbnail,
                        "get_capability": get_capability
                    }))

        items.sort(key=lambda x: x[0].lower())

        for title, dataset_id, metadata in items:
            self.datasetComboBox.addItem(title, dataset_id)
            self.dataset_metadata[dataset_id] = metadata

        self.update_dataset_details()
        self.loadingOverlay.hide()


    def show_query_parameters(self):
        self.clear_old_widgets()

        selected = self.datasetComboBox.currentData()
        if not selected:
            return

        self.loadingOverlay.show("🔄 Loading query parameters...")
        QApplication.processEvents()

        queryable = self.client.get("dataaccess", "queryable", selected)
        self.fields = build_field_definitions(queryable)

        metadata = self.dataset_metadata.get(selected, {})
        temp_begin = metadata.get("tempextent_begin")
        temp_end = metadata.get("tempextent_end")

        self.widgets.clear()
        self.formLayout.setSpacing(10)

        fields_not_to_show = ["itemsPerPage", "startIndex"]
        required_fields = queryable.get("required", [])
        self.required_field_names = required_fields  # Used in validation later

        notice_label = QLabel("Required fields are marked with a red *")
        notice_label.setStyleSheet("color: #666666; font-style: italic; margin-bottom: 10px;")
        self.formLayout.insertWidget(0, notice_label)
        


        for field in self.fields:
            if field["name"] in fields_not_to_show:
                continue

            name = field["name"]
            is_required = name in required_fields

            if is_required:
                label_text = f'{field["label"]}: <span style="color:red">*</span>'
            else:
                label_text = f'{field["label"]}:'

            label = QLabel()
            label.setTextFormat(Qt.RichText)  # aktiverer HTML
            label.setText(label_text)

            widget = None
            layout = QVBoxLayout(self)

            # Multi-selection list (e.g., 'variable')
            if field.get("items", {}).get("oneOf"):
                widget = QListWidget()
                widget.setSelectionMode(QListWidget.MultiSelection)

                # Add empty option at the top
                empty_item = QListWidgetItem("<None>")
                empty_item.setData(Qt.UserRole, None)
                widget.addItem(empty_item)

                for item in field["items"]["oneOf"]:
                    list_item = QListWidgetItem(item["title"])
                    list_item.setData(Qt.UserRole, item["const"])
                    widget.addItem(list_item)

            # ComboBox with fixed choices (e.g., 'month', 'year', 'data_format')
            elif field.get("choices"):
                widget = QComboBox()
                widget.addItem("<None>", None)  # Add blank choice

                for item in field["choices"]:
                    title = item.get("title", item.get("const", ""))
                    const = item.get("const", "")
                    widget.addItem(title, const)

                if widget.count() == 2: #blank + 1 value
                    widget.setCurrentIndex(1)
                    widget.setDisabled(True)

            # Datetime field (e.g., temporal extent)
            elif field.get("format") == "date-time":
                widget = NullableDateTimeInput()

                # Start‐felt
                start_w = NullableDateTimeInput()
                if temp_begin:
                    start_w.line.setText(f"{temp_begin}T00:00:00")
                layout.addWidget(start_w)

                # Slut‐felt
                end_w = NullableDateTimeInput()
                if temp_end:
                    end_w.line.setText(f"{temp_end}T23:59:59")
                layout.addWidget(end_w)

                self.setLayout(layout)

            # Bounding box field
            elif name.lower() == "bbox":
                widget = BoundingBoxWidget()

            # Default single-line text field
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("<Optional>")

            self.widgets[name] = widget
            self.formLayout.addWidget(label)
            self.formLayout.addWidget(widget)

        self.loadingOverlay.hide()


    def validate_required_fields(self):
        """
        Checks if all required fields have a value. Returns True if OK, otherwise shows a warning and returns False.
        """
        missing_fields = []

        for name in self.required_field_names:
            widget = self.widgets.get(name)

            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    missing_fields.append(name)

            elif isinstance(widget, QComboBox):
                if widget.currentData() in (None, ""):
                    missing_fields.append(name)

            elif isinstance(widget, QListWidget):
                if not any(item.isSelected() and item.data(Qt.UserRole) for item in widget.selectedItems()):
                    missing_fields.append(name)

            elif isinstance(widget, BoundingBoxWidget):
                if not widget.has_valid_bbox():
                    missing_fields.append(name)

            elif isinstance(widget, QDateTimeEdit):
                # Assuming always has a value; skip unless you want additional range checking
                pass

        if missing_fields:
            missing_list = ", ".join(missing_fields)
            QMessageBox.warning(None, "Missing required fields", f"The following required fields are missing:\n{missing_list}")
            return False

        return True

    def build_query(self):
        """
        Builds and returns the query dict from current form values.
        Also sets self.query for later use.
        """
        dataset_id = self.datasetComboBox.currentData()
        if not dataset_id:
            return None  # or raise ValueError("No dataset selected")

        query = {"dataset_id": dataset_id}

        for field in self.fields:
            name = field["name"]
            widget = self.widgets.get(name)
            if widget is None:
                continue

            # 1) Plain text
            if isinstance(widget, QLineEdit):
                val = widget.text().strip() or None

            # 2) Dropdowns
            elif isinstance(widget, QComboBox):
                val = widget.currentData() or None

            # 3) Native QDateTimeEdit (if you still use it elsewhere)
            elif isinstance(widget, QDateTimeEdit):
                # always emit UTC ISO with ms and Z
                dt = widget.dateTime().toUTC()
                val = dt.toString("yyyy-MM-dd'T'HH:mm:ss.zzz'Z'")

            # 4) Your nullable custom picker
            elif isinstance(widget, NullableDateTimeInput):
                iso_txt = widget.get_nullable()  # either None or "yyyy-MM-ddTHH:mm:ss"
                if iso_txt:
                    # parse local, convert to UTC, format with ms + Z
                    dt = QDateTime.fromString(iso_txt, "yyyy-MM-ddTHH:mm:ss")
                    dt = dt.toUTC()
                    val = dt.toString("yyyy-MM-dd'T'HH:mm:ss.zzz'Z'")
                else:
                    val = None

            # 5) Bounding box shape
            elif isinstance(widget, BoundingBoxWidget):
                val = widget.get_bbox() or None

            # 6) Multi-select lists
            elif isinstance(widget, QListWidget):
                items = [item.data(Qt.UserRole)
                        for item in widget.selectedItems()
                        if item.data(Qt.UserRole) is not None]
                val = items or None

            else:
                val = None

            # only add non-empty values
            if val is not None:
                query[name] = val

        self.query = query
        return query

    def show_request(self):
        query = self.build_query()
        if not query:
            QMessageBox.warning(self, "Error", "Query could not be built.")
            return

        json_string = json.dumps(query, indent=2)

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Current Query Parameters")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        # Text area
        text_edit = QTextEdit()
        text_edit.setText(json_string)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        # Buttons: Close + Copy
        buttons = QDialogButtonBox()
        copy_button = QPushButton("Copy to Clipboard")
        close_button = QPushButton("Close")
        buttons.addButton(copy_button, QDialogButtonBox.ActionRole)
        buttons.addButton(close_button, QDialogButtonBox.RejectRole)
        layout.addWidget(buttons)

        # Actions
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(text_edit.toPlainText()))
        close_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Query copied to clipboard.")

    def request_data(self):
        if self.client._access_token is None:
            QMessageBox.information(
                self,
                "WEkEO log in",
                "You are not logged in.\n\n"
                "Check if username and password are correct.\n\n"
                "Please click OK to open the login dialog and enter your credentials."
            )
            self.show_user_settings(self)
            return

        dataset_id = self.datasetComboBox.currentData()
        if not dataset_id:
            QMessageBox.warning(self, "Error", "Please select a dataset first.")
            return

        if not self.validate_required_fields():
            return  # Stop if required fields are missing

        self.loadingOverlay.show("🔄 Loading requested data...")
        QApplication.processEvents()

        try:
            term = self.dataset_metadata[dataset_id]["terms"][0]
        except (KeyError, IndexError):
            QMessageBox.warning(self, "Error", "Terms metadata missing.")
            self.loadingOverlay.hide()
            return

        if self.check_term(term):
            print("Term accepted.")
        else:
            print("Term not accepted.")

            QMessageBox.information(
                self,
                "Terms and Conditions",
                "You need to accept the terms and conditions before requesting data.\n\n"
                f"{term.replace('_', ' ')}\n\n"
                "Please click OK to open the terms dialog and then try requesting again."
            )
            self.open_terms_dialog(term)
            self.loadingOverlay.hide()
            return

        query = self.build_query()
        if not query:
            self.loadingOverlay.hide()
            return
        print(query)

        try:
            search_limit = int(self.limitLineEdit.text())
            if search_limit == 0:
                search_limit = None

            self.results = self.client.search(self.query, search_limit)
            self.match_results = []

            for match in self.results:
                try:
                    feature = match.results[0]
                    self.match_results.append({
                        "id": feature["id"],
                        "match": match
                    })
                except Exception as e:
                    log_message(f"Error handling match: {e}", "Copernicus Connect", "WARNING")

            self.fileListWidget.clear()
            for item in self.match_results:
                feature_id = item["id"]
                size = item["match"].results[0]["properties"].get("size")

                if isinstance(size, int):
                    size = format_size(size)

                label = f"{feature_id}\t{size})"
                self.fileListWidget.addItem(label)

            total_volume = self.results.volume
            if isinstance(total_volume, int):
                total_volume = format_size(total_volume)

            self.loadingOverlay.hide()

            message = f"Found {len(self.match_results)} results.\nSize: {total_volume}"
            if search_limit is not None and len(self.match_results) >= search_limit:
                message += (
                    f"\nThe number of matches has reached the limit of {search_limit}. "
                    "There may be additional matches."
                )

            QMessageBox.information(self, "Search complete", message)

        except Exception as e:
            self.loadingOverlay.hide()
            log_message(f"Error during search: {e}", "Copernicus Connect", "ERROR")
            QMessageBox.critical(self, "Search error", str(e))

    
    def get_download_path(self):
        pathfile = Path.home() / ".hda_path"
        if pathfile.is_file():
            with open(pathfile, 'r') as f:
                return Path(f.read().strip())
        return Path.home() / "HDA_Downloads"
   
 
    def show_user_settings(self):
        if get_user_credentials(self):
            print("Credentials saved.")
        else:
            print("Dialog canceled.")

    def show_path_settings(self):    
        dialog = PathDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            print("Path saved.")
        else:
            print("User canceled path setting.")

    def open_limit_dialog(self):
        dialog = LimitDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "Limit Saved", "New search limit has been saved.")

    def check_term(self, term):
        try:
            response = self.client.get("termsaccepted")
            features = response.get("features", [])

            for feature in features:
                if feature.get("term_id") == term:
                    return feature.get("accepted", False)

            # Hvis ikke fundet
            return False

        except Exception as e:
            print(f"Eror getting terms: {e}")
            return False


    def download_selected_files(self):

        if not hasattr(self, "match_results") or not self.match_results:
            log_message("match_results is empty!", "Copernicus Connect", "ERROR")
            QMessageBox.warning(self, "No data", "You must perform a search before downloading.")
            return

        selected_items = self.fileListWidget.selectedItems()
        selected_ids = [item.text().split()[0] for item in selected_items]

        if not selected_ids:
            QMessageBox.information(self, "No selection", "Please select at least one file to download.")
            return

        out_dir = self.get_download_path()
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log_message(f"Could not create directory: {e}", "Copernicus Connect", "CRITICAL")
            QMessageBox.critical(self, "Error", f"Could not create directory:\n{e}")
            return
        
        
        self.progressBar.setValue(0)
        self.statusLabel.setText("Status: Starting download...")

        try:
            self.worker = DownloadWorker(self.results, self.client, self.query, selected_ids, out_dir)
            self.worker.signals.progress.connect(self.progressBar.setValue)
            self.worker.signals.status.connect(lambda msg: self.statusLabel.setText(f"Status: {msg}"))
            self.worker.signals.error.connect(lambda err: QMessageBox.warning(self, "Error", err))
            self.worker.signals.finished.connect(self.download_finished)      

            QThreadPool.globalInstance().start(self.worker)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed:\n{e}")
               

def get_user_credentials(parent=None):
    dialog = UserDialog(parent)
    result = dialog.exec_()
    return result == QDialog.Accepted

def read_credentials():
    hdarc = Path.home() / ".hdarc"
    if not hdarc.is_file():
        return None, None

    credentials = {}
    with open(hdarc, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                credentials[key.strip()] = value.strip()

    username = credentials.get('user')
    password = credentials.get('password')

    if not username or not password:
        return None, None

    return username, password

def launch_form(parent=None):       
    
    username, password = read_credentials()

    if not username or not password:
        if not get_user_credentials(parent):
            return None
        username, password = read_credentials()

    try:
        conf = Configuration(user=username, password=password)
        hda_client = Client(config=conf)
        token = hda_client.token         
    except Exception as e:
        QMessageBox.information(parent,"Error", f"Login failed for {username}\n\n Please ensure your credentials are correct.")   
        username, password = read_credentials()
        conf = Configuration(user=username, password=password)
        hda_client = Client(config=conf)

    form = UiForm(hda_client)
    form.resize(800, 1000)
    form.show()
    form.load_datasets()

    return form

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = launch_form()
    sys.exit(app.exec_())
