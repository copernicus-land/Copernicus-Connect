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
        self.tool = None
        self.CANVAS_ITEM = "__CANVAS__"
        self._lastLayerId = None

        # Spinbokse
        self.northSpin = self._spinbox()
        self.southSpin = self._spinbox()
        self.eastSpin  = self._spinbox()
        self.westSpin  = self._spinbox()

        # Lag-combobox
        self.layerCombo = QComboBox()
        self.layerCombo.setMinimumWidth(250)
        self.layerCombo.currentIndexChanged.connect(self.on_layer_changed)

        # Kun én knap tilbage
        self.drawButton = QPushButton("Draw bounding box")
        self.drawButton.setMinimumWidth(160)
        self.drawButton.clicked.connect(self.draw_bounding_box)

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

        # Række med combobox + knap ved siden af hinanden
        row = QHBoxLayout()
        row.addWidget(self.drawButton)  
        row.addWidget(self.layerCombo, 1)  # combobox kan udvide sig
        row.addStretch() 

        # Endeligt layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        layout.addLayout(grid)
        layout.addLayout(row)
        self.setLayout(layout)

        # QGIS hooks
        if HAS_QGIS:
            QgsProject.instance().layersAdded.connect(self.populate_layer_combo)
            QgsProject.instance().layersRemoved.connect(self.populate_layer_combo)
            QgsProject.instance().layerWillBeRemoved.connect(self.populate_layer_combo)

        self.populate_layer_combo()


    # ---------- Hjælpemetoder ----------
    def _spinbox(self):
        s = QDoubleSpinBox()
        s.setDecimals(6)
        s.setRange(-180, 180)
        s.setSingleStep(0.1)
        s.setFixedWidth(90)
        return s

    def has_valid_bbox(self) -> bool:
        return self.get_bbox() is not None

    # ---------- BBOX værdier ----------
    def get_bbox(self):
        bbox = [self.westSpin.value(), self.southSpin.value(),
                self.eastSpin.value(), self.northSpin.value()]
        if bbox[0] == bbox[2] or bbox[1] == bbox[3]:
            return None
        return bbox

    def set_bbox_from_draw(self, minx, miny, maxx, maxy):
        self.westSpin.setValue(minx)
        self.southSpin.setValue(miny)
        self.eastSpin.setValue(maxx)
        self.northSpin.setValue(maxy)

    # ---------- Lagliste ----------
    def populate_layer_combo(self):
        self.layerCombo.blockSignals(True)
        try:
            # husk nuværende valg før vi rydder
            prev_id = None
            prev_data = self.layerCombo.currentData() if self.layerCombo.count() > 0 else None
            if prev_data == self.CANVAS_ITEM:
                prev_id = self.CANVAS_ITEM
            elif HAS_QGIS and prev_data is not None and hasattr(prev_data, "id"):
                prev_id = prev_data.id()
            elif getattr(self, "_lastLayerId", None):
                prev_id = self._lastLayerId

            self.layerCombo.clear()

            # 0) Dummy
            self.layerCombo.addItem("Select canvas/layer to copy", None)

            if HAS_QGIS:
                # 1) Canvas-valg
                self.layerCombo.addItem("— Extent from Canvas —", self.CANVAS_ITEM)

                # 2) Rigtige lag (filtrér 'AOI')
                layers = [
                    lyr for lyr in QgsProject.instance().mapLayers().values()
                    if hasattr(lyr, "extent")
                    and lyr.isValid()
                    and lyr.name().strip().lower() != "aoi"   # <-- filtrering
                ]
                layers.sort(key=lambda l: l.name().lower())
                for lyr in layers:
                    self.layerCombo.addItem(lyr.name(), lyr)

            # prøv at genskabe tidligere valg
            target_index = 0  # fallback = dummy
            if prev_id == self.CANVAS_ITEM:
                for i in range(self.layerCombo.count()):
                    if self.layerCombo.itemData(i) == self.CANVAS_ITEM:
                        target_index = i
                        break
            elif prev_id:
                for i in range(self.layerCombo.count()):
                    data = self.layerCombo.itemData(i)
                    if HAS_QGIS and data is not None and hasattr(data, "id") and data.id() == prev_id:
                        target_index = i
                        break

            self.layerCombo.setCurrentIndex(target_index)
        finally:
            self.layerCombo.blockSignals(False)


    def on_layer_changed(self, index: int):
        if index < 0:
            return
        data = self.layerCombo.itemData(index)

        self.clear_rectangle()
       
        if data is None:
            self._reset_bbox_spins()
            self.clear_rectangle()  
            return

        if data == self.CANVAS_ITEM:
            self.copy_from_map()
            return
       
        self.copy_from_layer()

    # ---------- Kopier extent ----------
    def copy_from_layer(self):
        if not HAS_QGIS:
            self._show_warning("Unavailable", "QGIS not available.")
            return
        layer = self.layerCombo.currentData()
        if not layer or layer == self.CANVAS_ITEM:
            return
        try:
            crs_src = layer.crs()
            crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
            ext = layer.extent()
            bl = xform.transform(QgsPointXY(ext.xMinimum(), ext.yMinimum()))
            tr = xform.transform(QgsPointXY(ext.xMaximum(), ext.yMaximum()))
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
            ext = canvas.extent()
            crs_src = canvas.mapSettings().destinationCrs()
            crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
            bl = xform.transform(QgsPointXY(ext.xMinimum(), ext.yMinimum()))
            tr = xform.transform(QgsPointXY(ext.xMaximum(), ext.yMaximum()))
            self.set_bbox_from_draw(bl.x(), bl.y(), tr.x(), tr.y())
        except Exception as e:
            self._show_warning("Error", f"Failed to copy extent from map:\n{str(e)}")

    # ---------- Tegneværktøj ----------
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
        self.clear_rectangle()
        self.deactivate_tool()
        canvas = iface.mapCanvas()
        self.tool = RectangleMapTool(canvas, self)
        canvas.setMapTool(self.tool)

        self.layerCombo.blockSignals(True)
        try:
            self.layerCombo.setCurrentIndex(0)
            self._reset_bbox_spins()   
        finally:
            self.layerCombo.blockSignals(False)

    def clear_rectangle(self):
        try:
            if self.tool and hasattr(self.tool, "clear_rectangle"):
                self.tool.clear_rectangle()
        except Exception:
            pass

    def _reset_bbox_spins(self):
        for s in (self.northSpin, self.southSpin, self.eastSpin, self.westSpin):
            s.blockSignals(True)
            s.setValue(0.0)
            s.blockSignals(False)

    def deactivate_tool(self):
        if not HAS_QGIS or self.tool is None:
            return
        try:
            from qgis.utils import iface
            canvas = getattr(iface, "mapCanvas", lambda: None)()
            if canvas and canvas.mapTool() is self.tool:
                canvas.unsetMapTool(self.tool)
        except Exception:
            pass
        finally:
            self.tool = None

    def cleanup(self):
        try:
            self.clear_rectangle()
        finally:
            self.deactivate_tool()

    def _show_warning(self, title, message):
        try:
            QMessageBox.warning(self, title, message)
        except Exception:
            print(f"[{title}] {message}")

