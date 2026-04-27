import os

try:
    from .qt_compat import QColor, QLabel, QPalette, QPixmap, QSize, Qt, QVBoxLayout, QWidget
except ImportError:
    from qt_compat import QColor, QLabel, QPalette, QPixmap, QSize, Qt, QVBoxLayout, QWidget

class LoadingOverlay(QWidget):
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        # Semi-transparent sort baggrund
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 75))
        self.setPalette(palette)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # PNG spinner/logo i QLabel
        png_path = os.path.join(os.path.dirname(__file__), 'resources', 'copernicus_logo.png')
        self.label_image = QLabel()
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setFixedSize(QSize(300, 109))

        pixmap = QPixmap(png_path).scaled(300, 109, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_image.setPixmap(pixmap)

        # Loading-tekst
        self.label_text = QLabel(message)
        self.label_text.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        self.label_text.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label_image)
        layout.addSpacing(12)  
        layout.addWidget(self.label_text)
        self.setLayout(layout)
        self.hide()

    def show(self, message="Loading..."):
        self.label_text.setText(message)
        self.resize(self.parent().size())
        self.move(0, 0)
        super().show()
        self.raise_()

    def hide(self):
        super().hide()
