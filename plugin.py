import os
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

class CopernicusConnectPlugin(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        icon = QIcon(icon_path)

 
        self.action = QAction(icon, "Copernicus Connect", self.iface.mainWindow())
        self.action.setToolTip("Copernicus Connect")
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)

        self.iface.pluginMenu().addAction(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.pluginMenu().removeAction(self.action)

    def run(self):
        from .main import launch_form
        form = launch_form(self.iface.mainWindow())
        if form:
            form.show()
