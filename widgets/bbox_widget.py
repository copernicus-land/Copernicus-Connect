try:
    from qgis.PyQt.QtWidgets import (
        QWidget, QDoubleSpinBox, QLabel, QGridLayout, QPushButton,
        QVBoxLayout, QMessageBox, QComboBox, QHBoxLayout
    )
    from qgis.PyQt.QtCore import Qt
    from qgis.core import (
        QgsProject,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsPointXY,
        QgsMapLayer
    )
    HAS_QGIS = True
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QDoubleSpinBox, QLabel, QGridLayout, QPushButton,
        QVBoxLayout, QMessageBox, QComboBox, QHBoxLayout
    )
    from PyQt5.QtCore import Qt
    HAS_QGIS = False


class BoundingBoxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(600)
        self.tool = None

        # Spinbokse
        self.northSpin = self._spinbox()
        self.southSpin = self._spinbox()
        self.eastSpin = self._spinbox()
        self.westSpin = self._spinbox()

        # Lag-dropdown og knapper
        self.layerCombo = QComboBox()
        self.layerCopyButton = QPushButton("Copy extent from selected layer")
        self.layerCopyButton.clicked.connect(self.copy_from_layer)

        self.copyButton = QPushButton("Copy extent from canvas")
        self.copyButton.clicked.connect(self.copy_from_map)

        self.drawButton = QPushButton("Draw bounding box")
        self.drawButton.clicked.connect(self.draw_bounding_box)

        self.clearButton = QPushButton("Remove bounding box")
        self.clearButton.clicked.connect(self.clear_rectangle)

        # Layout - BBOX grid
        grid = QGridLayout()
        grid.setContentsMargins(10, 10, 10, 0)
        grid.setSpacing(6)

        grid.addWidget(QLabel("N"), 0, 1, alignment=Qt.AlignRight)
        grid.addWidget(self.northSpin, 0, 2)

        grid.addWidget(QLabel("W"), 1, 0, alignment=Qt.AlignRight)
        grid.addWidget(self.westSpin, 1, 1)

        grid.addWidget(QLabel("E"), 1, 2, alignment=Qt.AlignRight)
        grid.addWidget(self.eastSpin, 1, 3, alignment=Qt.AlignLeft)

        grid.addWidget(QLabel("S"), 2, 1, alignment=Qt.AlignRight)
        grid.addWidget(self.southSpin, 2, 2)

        # Knapper under bbox
        buttonRowLayout = QHBoxLayout()
        for btn in (self.copyButton, self.drawButton, self.clearButton):
            btn.setMinimumWidth(160)
            buttonRowLayout.addWidget(btn)

        # Layervælger og knap
        layerLayout = QHBoxLayout()
        self.layerCombo.setMinimumWidth(250)
        self.layerCopyButton.setMinimumWidth(200)
        layerLayout.addWidget(self.layerCombo)
        layerLayout.addWidget(self.layerCopyButton)

        # Endeligt layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        layout.addLayout(grid)
        layout.addLayout(buttonRowLayout)
        layout.addSpacing(10)
        layout.addLayout(layerLayout)
        self.setLayout(layout)

        # QGIS hooks
        if HAS_QGIS:
            QgsProject.instance().layersAdded.connect(self.populate_layer_combo)
            QgsProject.instance().layersRemoved.connect(self.populate_layer_combo)
            QgsProject.instance().layerWillBeRemoved.connect(self.populate_layer_combo)

        self.populate_layer_combo()

    def _spinbox(self):
        spin = QDoubleSpinBox()
        spin.setDecimals(6)
        spin.setRange(-180, 180)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(90)
        return spin

    def get_bbox(self):
        bbox = [
            self.westSpin.value(),
            self.southSpin.value(),
            self.eastSpin.value(),
            self.northSpin.value()
        ]
        if bbox[0] == bbox[2] or bbox[1] == bbox[3]:
            return None
        return bbox

    def set_bbox_from_draw(self, minx, miny, maxx, maxy):
        self.westSpin.setValue(minx)
        self.southSpin.setValue(miny)
        self.eastSpin.setValue(maxx)
        self.northSpin.setValue(maxy)

    def populate_layer_combo(self):
        self.layerCombo.clear()
        if not HAS_QGIS:
            return
        layers = [
            layer for layer in QgsProject.instance().mapLayers().values()
            if hasattr(layer, "extent") and layer.isValid()
        ]
        layers.sort(key=lambda l: l.name().lower())
        for layer in layers:
            self.layerCombo.addItem(layer.name(), layer)

    def copy_from_layer(self):
        if not HAS_QGIS:
            self._show_warning("Unavailable", "QGIS not available.")
            return
        layer = self.layerCombo.currentData()
        if not layer:
            self._show_warning("No layer selected", "Please select a valid layer.")
            return
        try:
            crs_src = layer.crs()
            crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
            extent = layer.extent()
            bl = transform.transform(QgsPointXY(extent.xMinimum(), extent.yMinimum()))
            tr = transform.transform(QgsPointXY(extent.xMaximum(), extent.yMaximum()))
            self.set_bbox_from_draw(bl.x(), bl.y(), tr.x(), tr.y())
        except Exception as e:
            self._show_warning("Error", f"Failed to copy extent:\n{str(e)}")

    def copy_from_map(self):
        if not HAS_QGIS:
            self._show_warning("Unavailable", "QGIS not available.")
            return
        try:
            from qgis.utils import iface
        except ImportError:
            self._show_warning("Unavailable", "QGIS interface not available.")
            return

        if iface is None or not hasattr(iface, "mapCanvas"):
            self._show_warning("Unavailable", "QGIS interface not ready.")
            return

        try:
            canvas = iface.mapCanvas()
            extent = canvas.extent()
            crs_src = canvas.mapSettings().destinationCrs()
            crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
            bl = transform.transform(QgsPointXY(extent.xMinimum(), extent.yMinimum()))
            tr = transform.transform(QgsPointXY(extent.xMaximum(), extent.yMaximum()))
            self.set_bbox_from_draw(bl.x(), bl.y(), tr.x(), tr.y())
        except Exception as e:
            self._show_warning("Error", f"Failed to copy extent from map:\n{str(e)}")

    def draw_bounding_box(self):
        if not HAS_QGIS:
            self._show_warning("Unavailable", "QGIS not available.")
            return
        try:
            from qgis.utils import iface
            from .draw_rect import RectangleMapTool
        except ImportError:
            self._show_warning("Unavailable", "Required modules not available.")
            return

        if iface is None or not hasattr(iface, "mapCanvas"):
            self._show_warning("Unavailable", "QGIS interface not ready.")
            return

        canvas = iface.mapCanvas()
        self.clear_rectangle()
        self.tool = RectangleMapTool(canvas, self)
        canvas.setMapTool(self.tool)

    def clear_rectangle(self):
        if self.tool and hasattr(self.tool, "clear_rectangle"):
            self.tool.clear_rectangle()

    def _show_warning(self, title, message):
        try:
            QMessageBox.warning(self, title, message)
        except:
            print(f"[{title}] {message}")
