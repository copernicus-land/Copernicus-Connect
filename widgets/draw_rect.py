from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (
    QgsWkbTypes,
    QgsRectangle,
    QgsPointXY,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsFillSymbol,
    QgsSingleSymbolRenderer

)

class RectangleMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, dlg):
        super().__init__(canvas)
        self.canvas = canvas
        self.dlg = dlg

        self.startPoint = None
        self.endPoint = None
        self.isEmittingPoint = False
        self.last_geometry = None
        self.aoi_layer = None

        # Opret og tilføj rubberband (midlertidig visning)
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(QColor(0, 0, 255))
        self.rubberBand.setFillColor(QColor(0, 0, 255, 50))  # blå og transparent
        self.rubberBand.setBrushStyle(Qt.SolidPattern)
        self.rubberBand.setWidth(1)
        self.rubberBand.hide()

        self.init_aoi_layer()

    def init_aoi_layer(self):
        """Opretter AOI-lag med transparent stil og signalforbindelser."""
        if self.aoi_layer:
            QgsProject.instance().removeMapLayer(self.aoi_layer)

        canvas_crs = self.canvas.mapSettings().destinationCrs()
        self.aoi_layer = QgsVectorLayer(f"Polygon?crs={canvas_crs.authid()}", "AOI", "memory")
        self.aoi_provider = self.aoi_layer.dataProvider()

        # Transparent fill med blå kant
        symbol = QgsFillSymbol.createSimple({
            'color': '0,0,255,0',           # fill (blå + alpha)
            'outline_color': '0,0,255,255',  # kant (blå)
            'outline_width': '0.6'
        })
        self.aoi_layer.setRenderer(QgsSingleSymbolRenderer(symbol))

        QgsProject.instance().addMapLayer(self.aoi_layer)
        self.aoi_layer.startEditing()

        # Signalbaseret opdatering af bbox
        self.aoi_layer.featureAdded.connect(self.on_feature_change)
        self.aoi_layer.featureDeleted.connect(self.on_feature_change)
        self.aoi_layer.geometryChanged.connect(self.on_feature_change)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.rubberBand.show()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return
        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def _info(self, text):
        parent = self.dlg if getattr(self, "dlg", None) else self.canvas
        QMessageBox.information(parent, "Copernicus Connect", text)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        self.rubberBand.hide()
        r = self.rectangle()
        if r is None:
            return

        try:
            self.aoi_layer.startEditing()
            self.aoi_provider.truncate()
            geom = QgsGeometry.fromRect(r)
            self.feature = QgsFeature()
            self.feature.setGeometry(geom)
            self.aoi_provider.addFeature(self.feature)
            self.aoi_layer.updateExtents()
            self.aoi_layer.triggerRepaint()

            self.last_geometry = geom
            self.update_bbox_from_geom(geom)
        except:
            self._info("You must click the 'Draw bounding box' button first (AOI not initialized).")
            return


    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        points = [
            QgsPointXY(startPoint.x(), startPoint.y()),
            QgsPointXY(startPoint.x(), endPoint.y()),
            QgsPointXY(endPoint.x(), endPoint.y()),
            QgsPointXY(endPoint.x(), startPoint.y()),
            QgsPointXY(startPoint.x(), startPoint.y())
        ]

        for i, p in enumerate(points):
            self.rubberBand.addPoint(p, i == len(points) - 1)
        self.rubberBand.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None
        return QgsRectangle(self.startPoint, self.endPoint)

    def clear_rectangle(self):
        """Remove AOI layer (if present) and hide rubber band"""
        if self.aoi_layer and self.aoi_layer.isValid():
            QgsProject.instance().removeMapLayer(self.aoi_layer)
            self.aoi_layer = None
        self.last_geometry = None
        self.rubberBand.hide()



    def on_feature_change(self, *args):
        if not self.aoi_layer or not self.aoi_layer.isValid():
            return
        for feat in self.aoi_layer.getFeatures():
            geom = feat.geometry()
            if geom and (self.last_geometry is None or not geom.equals(self.last_geometry)):
                self.last_geometry = geom
                self.update_bbox_from_geom(geom)
                break

    def update_bbox_from_geom(self, geom):
        if geom is None or not geom.isGeosValid():
            print("Not ake valid bounding box")
            return
        rect = geom.boundingBox()

        crs_src = self.aoi_layer.crs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        xform = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())

        bottom_left = xform.transform(QgsPointXY(rect.xMinimum(), rect.yMinimum()))
        top_right = xform.transform(QgsPointXY(rect.xMaximum(), rect.yMaximum()))

        minx, miny = bottom_left.x(), bottom_left.y()
        maxx, maxy = top_right.x(), top_right.y()

        if hasattr(self.dlg, 'set_bbox_from_draw'):
            self.dlg.set_bbox_from_draw(minx, miny, maxx, maxy)

    def deactivate(self):
        QgsMapToolEmitPoint.deactivate(self)
        self.deactivated.emit()
