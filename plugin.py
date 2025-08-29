import os
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.gui import QgsDockWidget


class CopernicusConnectPlugin(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.action = None
        self.dock = None  # holds reference to the dock panel

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        icon = QIcon(icon_path)

        # Checkable action toggles dock visibility
        self.action = QAction(icon, "Copernicus Connect", self.iface.mainWindow())
        self.action.setToolTip("Copernicus Connect")
        self.action.setCheckable(True)
        self.action.toggled.connect(self.toggle_dock)

        # Add to toolbar and Plugins menu
        self.iface.addToolBarIcon(self.action)
        self.iface.pluginMenu().addAction(self.action)

    def unload(self):
        # Remove dock if it exists
        if self.dock:
            try:
                self.iface.removeDockWidget(self.dock)
            except Exception:
                pass
            self.dock.deleteLater()
            self.dock = None

        # Remove actions
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.pluginMenu().removeAction(self.action)
            self.action = None

    def toggle_dock(self, checked: bool):
        if checked:
            # Create the dock the first time
            if not self.dock:
                from .main import launch_form  # must return a QWidget as content
                content_widget = launch_form(self.iface.mainWindow())

                self.dock = QgsDockWidget("Copernicus Connect", self.iface.mainWindow())
                self.dock.setObjectName("CopernicusConnectDock")  # required so QGIS remembers placement
                self.dock.setAllowedAreas(
                    Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
                    Qt.TopDockWidgetArea  | Qt.BottomDockWidgetArea
                )
                self.dock.setWidget(content_widget)

                # Keep toolbar button state in sync if user hides the panel manually
                self.dock.visibilityChanged.connect(self.action.setChecked)

                # Register dock with QGIS (appears under View → Panels)
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

            self.dock.show()
            self.dock.raise_()
        else:
            if self.dock:
                self.dock.hide()

    # Keep run for legacy shortcuts; internally just toggles the panel
    def run(self):
        self.action.toggle()
