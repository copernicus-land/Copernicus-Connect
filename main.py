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
        # Always print to terminal as well
        print(f"[{level_str}] {tag}: {msg}")
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
    QLineEdit, QLabel, QDialog, QMessageBox, QListWidget, QListWidgetItem, QDockWidget, QToolButton, QHBoxLayout, QWidget, QSizePolicy

)
from PyQt5.QtCore import (QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QDateTime, Qt, QStringListModel, QModelIndex, QTimer)
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
import traceback
from PyQt5.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QIcon, QPixmap, QClipboard
from hda import Client, Configuration


UI_PATH = os.path.join(os.path.dirname(__file__), "resources", "form.ui")
base_path = os.path.dirname(os.path.abspath(__file__))
json_path_dataset = os.path.join(base_path, "resources", "dataset.json")
image_placeholder = os.path.join(base_path, "resources", "placeholder.png")

# Unified default timeout (seconds) for HDA client calls and overall guards
# Can be overridden with environment variable HDA_TIMEOUT
try:
    DEFAULT_CLIENT_TIMEOUT = int(os.environ.get("HDA_TIMEOUT", "60"))
except Exception:
    DEFAULT_CLIENT_TIMEOUT = 60




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
    def __init__(self, client, parent=None):
        super().__init__(parent)
        uic.loadUi(UI_PATH, self)
    
        # do not change the size of the combobox according to its content (title)
        self.datasetComboBox.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.datasetComboBox.setMinimumContentsLength(25)

        self.datasetComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        

        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Copernicus Connect")
        self.bboxWidget = None  # reference til aktiv BoundingBoxWidget

        self.loadingOverlay = LoadingOverlay(self.tabWidget) 

        if hasattr(self, "splitterQueryForm"):
            self.splitterQueryForm.setStretchFactor(1, 3)  # scrollArea
            self.splitterQueryForm.setStretchFactor(1, 1)  # controls below

     
        if hasattr(self, "splitterWMS"):
            self.splitterWMS.setStretchFactor(0, 3)  # treeViewWMS
            self.splitterWMS.setStretchFactor(1, 1)  # txt_info


        self.client = client
        self.fields = []
        self.required_field_names = []  # ensure attribute always exists
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
        self.selectButton.setIcon(QIcon(self.resource_path("icon", "select_all.ico")))
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
        self.actionWiki.triggered.connect(self.open_wiki_page)
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
        self.selectButton.clicked.connect(self.select_interval)
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

   
    def open_wiki_page(self):
        try:
            webbrowser.open('https://github.com/copernicus-land/Copernicus-Connect/wiki')
        except Exception as exc:
            QMessageBox.warning(self, 'Copernicus Connect', f'Could not open manual: {exc}')

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
            print("🧪 Simulation without QGIS:")
            print(f"Name: {layers_str}")
            print(f"URI: {uri}")
            
    
        return

    
    def select_all_items(self):
        count = self.fileListWidget.count()
        if count > 100:
            QMessageBox.warning(self, "Too many files", "WEkEO only supports 100 downloads per hour. Only the first 100 files will be selected.")
            self.fileListWidget.clearSelection()
            for i in range(100):
                item = self.fileListWidget.item(i)
                item.setSelected(True)
        else:
            self.fileListWidget.selectAll()

    def clear_selection(self):
        self.fileListWidget.clearSelection()

    def select_interval(self):
        """
        Select a range of files in fileListWidget based on txtFrom and txtTo.
        txtFrom and txtTo should be 1-based indices (first file = 1).
        """
        try:
            from_text = self.txtFrom.text().strip()
            to_text = self.txtTo.text().strip()
            if not from_text or not to_text:
                QMessageBox.warning(self, "Missing interval", "Please enter both 'From' and 'To' values.")
                return
            from_idx = int(from_text) - 1
            to_idx = int(to_text) - 1
            count = self.fileListWidget.count()
            if from_idx < 0 or to_idx < 0 or from_idx >= count or to_idx >= count:
                QMessageBox.warning(self, "Invalid interval", f"Interval must be between 1 and {count}.")
                return
            if from_idx > to_idx:
                from_idx, to_idx = to_idx, from_idx

            # Calculate dynamic max downloads left
            import datetime
            pathfile = Path.home() / ".hda_download_status"
            now = datetime.datetime.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            downloads_last_hour = 0
            if pathfile.is_file():
                try:
                    with open(pathfile, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) == 2:
                                ts_str, count_str = parts
                                try:
                                    ts = datetime.datetime.fromisoformat(ts_str)
                                    count = int(count_str)
                                    if ts > one_hour_ago:
                                        downloads_last_hour += count
                                except Exception:
                                    continue
                except Exception:
                    pass
            max_allowed = max(0, 100 - downloads_last_hour)
            interval_size = to_idx - from_idx + 1
            if interval_size > max_allowed:
                QMessageBox.warning(
                    self,
                    "Interval too large",
                    f"It is not allowed to select more than {max_allowed} files at once. WEkEO only supports 100 downloads per hour. You have already downloaded {downloads_last_hour} files in the last hour."
                )
                return
            self.fileListWidget.clearSelection()
            for i in range(from_idx, to_idx + 1):
                item = self.fileListWidget.item(i)
                item.setSelected(True)
        except Exception as e:
            QMessageBox.warning(self, "Interval selection error", f"An error occurred:\n{e}")

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

        if getattr(self, "bboxWidget", None) is not None:
            try:
                self.bboxWidget.clear_rectangle()
            except Exception:
                pass
            self.bboxWidget = None
        
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
        # Reset query state so user must load parameters again
        try:
            self.fields = []
            self.required_field_names = []
        except Exception:
            self.fields = []
        try:
            self.widgets.clear()
        except Exception:
            self.widgets = {}
        self.query = None
        self.results = []
        self.match_results = []
        self.fileListWidget.clear()
        self.txt_info.clear()
        self.progressBar.setValue(0)
        self.statusLabel.setText("Status: Ready")
  
        self.loadingOverlay.hide()

    def clear_old_widgets(self):
        # ryd evt. aktiv rektangel før vi fjerner widget
        if getattr(self, "bboxWidget", None) is not None:
            try:
                self.bboxWidget.clear_rectangle()
            except Exception:
                pass
            self.bboxWidget = None 

        for i in reversed(range(self.formLayout.count())):
            w = self.formLayout.itemAt(i).widget()
            if w:
                w.setParent(None)

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
            # If it's a timeout or network error, show message and abort so user can retry
            err_txt = str(e)
            if isinstance(e, Exception) and (
                'timed out' in err_txt.lower() or 'timeout' in err_txt.lower() or 'connection' in err_txt.lower()
            ):
                self.loadingOverlay.hide()
                log_message(f"Dataset load error: {e}", "Copernicus Connect", "ERROR")
                QMessageBox.warning(
                    self,
                    "Dataset load failed",
                    f"Could not load datasets due to a network/server error.\n\n{e}\n\nPlease try again."
                )
                return

            self.loadingOverlay.hide()

            if not get_user_credentials(self):
                QMessageBox.warning(self, "Login Failed", "Cannot load datasets without valid credentials.")
                return

            username, password = read_credentials()
            conf = Configuration(user=username, password=password)
            self.client = Client(config=conf)
            # Ensure the client doesn't hang indefinitely on requests
            try:
                _timeout = DEFAULT_CLIENT_TIMEOUT
            except NameError:
                _timeout = 30
            try:
                self.client.timeout = _timeout
            except Exception:
                pass

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
            #source = ds.get("metadata", {}).get("_source", {})
            source = ds.get("metadata", {})

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
            self.bboxWidget = None
            return

        self.loadingOverlay.show("🔄 Loading query parameters...")
        QApplication.processEvents()
        try:
            queryable = self.client.get("dataaccess", "queryable", selected)
        except Exception as e:
            # Hide overlay before showing any user dialog
            self.loadingOverlay.hide()
            err_text = str(e)
            log_message(f"Error loading queryable for {selected}: {err_text}", "Copernicus Connect", "ERROR")

            # If it's a timeout-like error, offer Retry/Cancel
            if (
                isinstance(e, requests.exceptions.ReadTimeout)
                or "timed out" in err_text.lower()
                or "timeout" in err_text.lower()
            ):
                choice = QMessageBox.question(
                    self,
                    "Timeout",
                    f"Loading query parameters timed out.\n\n{err_text}\n\nDo you want to try again?",
                    QMessageBox.Retry | QMessageBox.Cancel,
                    QMessageBox.Retry,
                )
                if choice == QMessageBox.Retry:
                    return self.show_query_parameters()
                return

            # Generic failure
            QMessageBox.critical(self, "Error", f"Could not load query parameters.\n\n{err_text}")
            return
        self.fields = build_field_definitions(queryable)

        metadata = self.dataset_metadata.get(selected, {})
        temp_begin = metadata.get("tempextent_begin")
        temp_end = metadata.get("tempextent_end")

        self.widgets.clear()
        self.formLayout.setSpacing(10)

        fields_not_to_show = ["itemsPerPage", "startIndex"]
        required_fields = queryable.get("required", [])
        self.required_field_names = required_fields

        notice_label = QLabel("Required fields are marked with a red *")
        notice_label.setStyleSheet("color: #666666; font-style: italic; margin-bottom: 10px;")
        self.formLayout.insertWidget(0, notice_label)

        # antag at der ikke er bbox, indtil vi ser det
        self.bboxWidget = None

        for field in self.fields:
            if field["name"] in fields_not_to_show:
                continue

            name = field["name"]
            is_required = name in required_fields

            label = QLabel()
            label.setTextFormat(Qt.RichText)
            label.setText(f'{field["label"]}: ' + ('<span style="color:red">*</span>' if is_required else ''))

            widget = None

            # Multi-selection
            if field.get("items", {}).get("oneOf"):
                widget = QListWidget()
                widget.setSelectionMode(QListWidget.MultiSelection)
                empty_item = QListWidgetItem("<None>")
                empty_item.setData(Qt.UserRole, None)
                widget.addItem(empty_item)
                for item in field["items"]["oneOf"]:
                    li = QListWidgetItem(item["title"])
                    li.setData(Qt.UserRole, item["const"])
                    widget.addItem(li)

            # Choices (combobox)
            elif field.get("choices"):
                widget = QComboBox()
                widget.addItem("<None>", None)
                for item in field["choices"]:
                    title = item.get("title", item.get("const", ""))
                    const = item.get("const", "")
                    widget.addItem(title, const)
                if widget.count() == 2:
                    widget.setCurrentIndex(1)
                    widget.setDisabled(True)

            # Datetime
            elif field.get("format") == "date-time":
                # Behold én widget (NullableDateTimeInput). Du lavede også start/end før,
                # men hvis skemaet kun forventer ét felt, så brug én.
                widget = NullableDateTimeInput()
                # evt. forudfyld:
                if temp_begin and "start" in name.lower():
                    widget.line.setText(f"{temp_begin}T00:00:00")
                if temp_end and "end" in name.lower():
                    widget.line.setText(f"{temp_end}T23:59:59")

            # BBOX
            elif name.lower() == "bbox":
                widget = BoundingBoxWidget(self)
                self.bboxWidget = widget  # <- GEM REFERENCE

            # Default text
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("<Optional>")

            self.widgets[name] = widget
            self.formLayout.addWidget(label)
            self.formLayout.addWidget(widget)

        # Hide the overlay once all widgets are added
        self.loadingOverlay.hide()



    def validate_required_fields(self):
        """
        Checks if all required fields have a value. Returns True if OK, otherwise shows a warning and returns False.
        """
        missing_fields = []

        # Ensure query parameters are loaded
        if not hasattr(self, "required_field_names") or not self.required_field_names:
            QMessageBox.information(
                self,
                "Parameters not loaded",
                "Please click 'Show Query Parameters' to load the available fields before requesting data."
            )
            return False

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
        # Show a loading overlay while preparing the request preview
        self.loadingOverlay.show("🔄 Preparing API request…")
        self.loadingOverlay.raise_()
        QTimer.singleShot(0, self.loadingOverlay.repaint)
        QApplication.processEvents()

        try:
            query = self.build_query()
            if not query:
                QMessageBox.warning(self, "Error", "Query could not be built.")
                return

            json_string = json.dumps(query, indent=2)
        finally:
            # Hide overlay before showing the dialog so it doesn't cover it
            self.loadingOverlay.hide()

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Current Query Parameters")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        # Text area (editable)
        text_edit = QTextEdit()
        text_edit.setText(json_string)
        text_edit.setReadOnly(False)
        layout.addWidget(text_edit)

        # Buttons: Close + Copy + Run
        buttons = QDialogButtonBox()
        copy_button = QPushButton("Copy to Clipboard")
        close_button = QPushButton("Close")
        run_button = QPushButton("Run This Query")
        buttons.addButton(copy_button, QDialogButtonBox.ActionRole)
        buttons.addButton(run_button, QDialogButtonBox.ActionRole)
        buttons.addButton(close_button, QDialogButtonBox.RejectRole)
        layout.addWidget(buttons)

        # Actions
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(text_edit.toPlainText()))
        run_button.clicked.connect(lambda: self.run_query_from_json_text(text_edit.toPlainText(), parent_dialog=dialog))
        close_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Query copied to clipboard.")

    def open_run_query_dialog(self):
        """Open a dialog to paste raw JSON and execute it as a query."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Run Query from JSON")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        label = QLabel("Paste a JSON query (must include 'dataset_id'):")
        layout.addWidget(label)

        text_edit = QTextEdit()
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox()
        run_button = QPushButton("Run Query")
        cancel_button = QPushButton("Cancel")
        buttons.addButton(run_button, QDialogButtonBox.AcceptRole)
        buttons.addButton(cancel_button, QDialogButtonBox.RejectRole)
        layout.addWidget(buttons)

        run_button.clicked.connect(lambda: self.run_query_from_json_text(text_edit.toPlainText(), parent_dialog=dialog))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def _set_current_dataset(self, dataset_id):
        """Try to select the dataset in the combo by dataset_id. Returns True if found."""
        if not dataset_id:
            return False
        for i in range(self.datasetComboBox.count()):
            if self.datasetComboBox.itemData(i) == dataset_id:
                if self.datasetComboBox.currentIndex() != i:
                    self.datasetComboBox.setCurrentIndex(i)
                    # Optionally refresh details
                    try:
                        self.update_dataset_details()
                    except Exception:
                        pass
                return True
        return False

    def run_query_from_json_text(self, text, parent_dialog=None):
        """Parse raw JSON text and run it via send_query()."""
        try:
            query = json.loads(text)
            if not isinstance(query, dict):
                raise ValueError("JSON must be an object with fields, including 'dataset_id'.")
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not parse JSON query:\n{e}")
            return

        dataset_id = query.get("dataset_id")
        if not dataset_id:
            QMessageBox.warning(self, "Missing dataset_id", "The query must include a 'dataset_id' field.")
            return

        found = self._set_current_dataset(dataset_id)
        if not found:
            QMessageBox.warning(
                self,
                "Dataset not loaded",
                f"Dataset '{dataset_id}' is not in the current list. The request may fail if terms/metadata are missing."
            )

        # Close the parent dialog (if any) before running to show overlay cleanly
        if parent_dialog is not None:
            # Show overlay immediately when the user chooses to run the query
            self.loadingOverlay.show("🔄 Running query…")
            self.loadingOverlay.raise_()
            QTimer.singleShot(0, self.loadingOverlay.repaint)
            QApplication.processEvents()
            try:
                parent_dialog.accept()
            except Exception:
                pass

        # Use the helper that bypasses UI validation
        self.send_query(query)

    # --- Helper methods for request flow ---
    def _ensure_logged_in(self):
        if getattr(self.client, "_access_token", None) is None:
            QMessageBox.information(
                self,
                "WEkEO log in",
                "You are not logged in.\n\n"
                "Check if username and password are correct.\n\n"
                "Please click OK to open the login dialog and enter your credentials."
            )
            # Keep existing call style to avoid broader changes
            try:
                self.show_user_settings(self)
            except TypeError:
                # Fallback to the no-arg signature if defined that way
                self.show_user_settings()
            return False
        return True

    def _resolve_dataset_id(self, query):
        if isinstance(query, dict) and query.get("dataset_id"):
            return query["dataset_id"]
        return self.datasetComboBox.currentData()

    def _ensure_terms_for_dataset(self, dataset_id):
        try:
            term = self.dataset_metadata[dataset_id]["terms"][0]
        except (KeyError, IndexError, TypeError):
            QMessageBox.warning(self, "Error", "Terms metadata missing.")
            return False

        result = self.check_term(term)
        if result is None:
            # Error already shown to user; stop flow so they can retry
            return False
        if result:
            return True

        QMessageBox.information(
            self,
            "Terms and Conditions",
            "You need to accept the terms and conditions before requesting data.\n\n"
            f"{term.replace('_', ' ')}\n\n"
            "Please click OK to open the terms dialog and then try requesting again."
        )
        self.open_terms_dialog(term)
        return False

    def _parse_search_limit(self):
        try:
            limit_val = int(self.limitLineEdit.text())
        except Exception:
            limit_val = 0
        return None if limit_val == 0 else limit_val

    def _search_with_timeout(self, query, search_limit, seconds=None):
        """Run client.search with a hard overall timeout.

        This guards against cases where the HDA client retries/backoffs or polls
        for too long despite per-request timeouts.
        """
        if seconds is None:
            try:
                seconds = DEFAULT_CLIENT_TIMEOUT
            except NameError:
                seconds = 60
        # IMPORTANT: Do NOT use a context manager here, since exiting a
        # ThreadPoolExecutor context performs a blocking shutdown(wait=True).
        # That would freeze the UI after a timeout. We manage shutdown manually.
        ex = ThreadPoolExecutor(max_workers=1)
        fut = ex.submit(self.client.search, query, search_limit)
        timed_out = False
        try:
            return fut.result(timeout=seconds)
        except FuturesTimeout:
            timed_out = True
            try:
                fut.cancel()
            except Exception:
                pass
            # Do not block the UI waiting for search to finish
            try:
                ex.shutdown(wait=False)
            except Exception:
                pass
            raise TimeoutError(f"Search timed out after {seconds} seconds")
        finally:
            # If not timed out, we can shut down cleanly and wait for completion
            if not timed_out:
                try:
                    ex.shutdown(wait=True)
                except Exception:
                    pass

    def _populate_results_ui(self, search_limit):
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

        total_volume = getattr(self.results, "volume", None)
        if isinstance(total_volume, int):
            total_volume = format_size(total_volume)

        message = f"Found {len(self.match_results)} results.\nSize: {total_volume}"
        if search_limit is not None and len(self.match_results) >= search_limit:
            message += (
                f"\nThe number of matches has reached the limit of {search_limit}. "
                "There may be additional matches."
            )
        QMessageBox.information(self, "Search complete", message)

    def send_query(self, query):
        """Public helper: run a provided query dict without UI validation."""
        return self.request_data(query=query, skip_validation=True)

    def request_data(self, checked=False, query=None, skip_validation=False):
        """
        Request data based on current UI or a provided query.

        - If 'query' is provided, it is used directly and UI validation is skipped
          unless 'skip_validation' is False.
        - If 'query' is None, the query is built from the current UI widgets.
        """
        # 1) Ensure logged in
        if not self._ensure_logged_in():
            return

        # 2) Resolve dataset id from query or UI
        dataset_id = self._resolve_dataset_id(query)
        if not dataset_id:
            QMessageBox.warning(self, "Error", "Please select a dataset first.")
            return

        # 3) Validate required fields only if using UI-driven build and not skipping
        if query is None and not skip_validation:
            # Ensure parameters are loaded (user clicked 'Show Query Parameters')
            if not self.fields or not getattr(self, "required_field_names", []):
                QMessageBox.information(
                    self,
                    "Parameters not loaded",
                    "Please click 'Show Query Parameters' to load the available fields before requesting data."
                )
                return
            if not self.validate_required_fields():
                return

        self.loadingOverlay.show("🔄 Loading requested data...")
        QApplication.processEvents()

        try:
            # 4) Ensure terms accepted for dataset
            if not self._ensure_terms_for_dataset(dataset_id):
                return

            # 5) Build or set query
            if query is None:
                query = self.build_query()
            self.query = query
            if not self.query:
                return

            # 6) Execute search (with hard timeout)
            search_limit = self._parse_search_limit()
            self.results = self._search_with_timeout(self.query, search_limit)

            # 7) Populate results in UI
            self._populate_results_ui(search_limit)

        except Exception as e:
            # Ensure overlay is hidden before showing any dialogs
            self.loadingOverlay.hide()

            err_text = str(e)
            log_message(f"Error during search: {err_text}", "Copernicus Connect", "ERROR")

            # Specific handling for timeouts: offer Retry/Cancel
            if isinstance(e, TimeoutError) or "timed out" in err_text.lower():
                choice = QMessageBox.question(
                    self,
                    "Search timed out",
                    f"The search did not finish within the time limit.\n\n{err_text}\n\nDo you want to try again?",
                    QMessageBox.Retry | QMessageBox.Cancel,
                    QMessageBox.Retry,
                )
                if choice == QMessageBox.Retry:
                    # Re-run with the same query; skip UI validation since it's already built
                    # and terms were already checked in this flow.
                    return self.request_data(query=self.query if query is None else query, skip_validation=True)
                return

            # Default error dialog for non-timeout errors
            QMessageBox.critical(self, "Search error", err_text)
        finally:
            # Keep as a safety; already hidden above on error
            self.loadingOverlay.hide()

    
    def get_download_path(self):
        pathfile = Path.home() / ".hda_path"
        if pathfile.is_file():
            with open(pathfile, 'r') as f:
                return Path(f.read().strip())
        return Path.home() / "HDA_Downloads"
   
 
    def show_user_settings(self):
        if not get_user_credentials(self):
            print("Dialog canceled.")
            return

        # Read newly saved credentials
        username, password = read_credentials()
        if not username or not password:
            QMessageBox.warning(self, "Login", "Username or password missing.")
            return

        # Show a short overlay while logging in
        self.loadingOverlay.show("🔐 Logging in…")
        QApplication.processEvents()

        try:
            conf = Configuration(user=username, password=password)
            new_client = Client(config=conf)
            try:
                _timeout = DEFAULT_CLIENT_TIMEOUT
            except NameError:
                _timeout = 30
            try:
                new_client.timeout = _timeout
            except Exception:
                pass
            # Force a token retrieval to validate credentials
            _ = new_client.token
        except Exception as e:
            self.loadingOverlay.hide()
            QMessageBox.critical(self, "Login failed", f"Could not log in with the provided credentials.\n\n{e}")
            return

        # Swap client and load datasets
        self.client = new_client
        self.loadingOverlay.hide()
        try:
            self.load_datasets()
        except Exception:
            # load_datasets handles its own user feedback and overlay
            pass

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

            return False

        except Exception as e:
            log_message(f"Error getting terms: {e}", "Copernicus Connect", "ERROR")
            try:
                QMessageBox.warning(
                    self,
                    "Terms check failed",
                    f"Could not verify terms due to a network/server error.\n\n{e}\n\nPlease try again."
                )
            except Exception:
                pass
            return None
        
    def save_download_status(self, selected_ids):
        """
        Save the count and timestamp of downloads to a file, keeping only entries from the last hour.
        Each line: <timestamp_iso> <count>
        """
        import datetime
        pathfile = Path.home() / ".hda_download_status"
        now = datetime.datetime.now()
        one_hour_ago = now - datetime.timedelta(hours=1)
        entries = []
        # Read existing entries
        if pathfile.is_file():
            try:
                with open(pathfile, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            ts_str, count_str = parts
                            try:
                                ts = datetime.datetime.fromisoformat(ts_str)
                                count = int(count_str)
                                if ts > one_hour_ago:
                                    entries.append((ts, count))
                            except Exception:
                                continue
            except Exception as e:
                log_message(f"Could not read download status: {e}", "Copernicus Connect", "WARNING")
        # Add new entry
        entries.append((now, len(selected_ids)))
        # Write back only entries within last hour
        try:
            with open(pathfile, 'w') as f:
                for ts, count in entries:
                    f.write(f"{ts.isoformat()} {count}\n")
        except Exception as e:
            log_message(f"Could not save download status: {e}", "Copernicus Connect", "WARNING")


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

            self.save_download_status(selected_ids)

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

from PyQt5.QtWidgets import QApplication, QMessageBox

def launch_form(parent=None):
    # Ensure there's a QApplication when running outside QGIS
    app_created = False
    if QApplication.instance() is None:
        # Only create an app if we're not inside QGIS
        try:
            # running_in_qgis is set in your try/except import block
            if not running_in_qgis:
                _ = QApplication([])  # minimal app; main loop started elsewhere if needed
                app_created = True
        except NameError:
            # Fallback if the flag isn't defined for some reason
            _ = QApplication([])
            app_created = True

    # 1) Create client with stored creds (empty allowed) and try validate
    username, password = read_credentials()
    username = username or ""
    password = password or ""

    conf = Configuration(user=username, password=password)
    hda_client = Client(config=conf)
    try:
        _timeout = DEFAULT_CLIENT_TIMEOUT
    except NameError:
        _timeout = 30
    try:
        hda_client.timeout = _timeout
    except Exception:
        pass

    logged_in = False
    # If creds exist, try to validate; otherwise prompt
    need_prompt = not (username and password)
    if not need_prompt:
        try:
            _ = hda_client.token
            logged_in = True
        except Exception:
            need_prompt = True

    if need_prompt:
        # Ask for credentials but do not block plugin launch if cancelled
        if get_user_credentials(parent):
            # Read and try again
            new_user, new_pass = read_credentials()
            if new_user and new_pass:
                try:
                    new_conf = Configuration(user=new_user, password=new_pass)
                    new_client = Client(config=new_conf)
                    try:
                        new_client.timeout = _timeout
                    except Exception:
                        pass
                    _ = new_client.token
                    hda_client = new_client
                    logged_in = True
                except Exception:
                    # Keep plugin open; user can retry later from menu
                    QMessageBox.information(
                        parent,
                        "Login failed",
                        "Could not log in with the provided credentials. You can try again from the User menu."
                    )
        # else: user cancelled — proceed without login

    # 3) Create and return the form (do not show/resize here)
    form = UiForm(hda_client, parent=parent)

    # Load datasets early only if we are logged in
    if hasattr(form, "load_datasets") and logged_in:
        try:
            form.load_datasets()
        except Exception:
            pass

    # If we created an app just for a quick test run and want to show the window when
    # running outside QGIS, you can (optionally) show it here:
    if app_created and not running_in_qgis:
        form.show()

    return form


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication.instance() or QApplication(sys.argv)

    form = launch_form()  # parent=None i standalone
    if form is None:
        print("Launch cancelled/failed (no credentials or login error).")
        sys.exit(0)

    form.show()  # <- VIGTIGT i standalone
    sys.exit(app.exec_())
