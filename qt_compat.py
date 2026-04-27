"""Qt compatibility helpers for QGIS 3.x/4.x and standalone development."""

try:
    from qgis.PyQt import uic
    from qgis.PyQt.QtCore import (
        QModelIndex,
        QObject,
        QRunnable,
        QSize,
        QStringListModel,
        QThreadPool,
        QTimer,
        QDateTime,
        Qt,
        pyqtSignal,
        pyqtSlot,
    )
    from qgis.PyQt.QtGui import (
        QAction,
        QColor,
        QClipboard,
        QIcon,
        QIntValidator,
        QPalette,
        QPixmap,
        QStandardItem,
        QStandardItemModel,
    )
    from qgis.PyQt.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QDateTimeEdit,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QDoubleSpinBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QStyle,
        QTextBrowser,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PyQt5 import uic
    from PyQt5.QtCore import (
        QModelIndex,
        QObject,
        QRunnable,
        QSize,
        QStringListModel,
        QThreadPool,
        QTimer,
        QDateTime,
        Qt,
        pyqtSignal,
        pyqtSlot,
    )
    from PyQt5.QtGui import (
        QColor,
        QClipboard,
        QIcon,
        QIntValidator,
        QPalette,
        QPixmap,
        QStandardItem,
        QStandardItemModel,
    )
    from PyQt5.QtWidgets import (
        QAction,
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QDateTimeEdit,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QDoubleSpinBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QStyle,
        QTextBrowser,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )


def _alias_enum(cls, legacy_name, enum_name, value_name=None):
    if hasattr(cls, legacy_name):
        return
    enum_cls = getattr(cls, enum_name, None)
    if enum_cls is None:
        return
    value = getattr(enum_cls, value_name or legacy_name, None)
    if value is not None:
        setattr(cls, legacy_name, value)


def _alias_value(cls, legacy_name, value):
    if not hasattr(cls, legacy_name) and value is not None:
        setattr(cls, legacy_name, value)


def _alias_qt(legacy_name, enum_name):
    _alias_enum(Qt, legacy_name, enum_name)


for _name in (
    "Fixed",
    "Minimum",
    "Maximum",
    "Preferred",
    "Expanding",
    "MinimumExpanding",
    "Ignored",
):
    _alias_enum(QSizePolicy, _name, "Policy")

for _name in (
    "SP_ArrowDown",
    "SP_BrowserReload",
    "SP_DialogCancelButton",
    "SP_DialogOpenButton",
    "SP_DialogSaveButton",
    "SP_DirOpenIcon",
    "SP_FileDialogContentsView",
    "SP_FileDialogDetailedView",
    "SP_FileIcon",
):
    _alias_enum(QStyle, _name, "StandardPixmap")

for _name in ("Ok", "Cancel", "Save", "Close"):
    _alias_enum(QDialogButtonBox, _name, "StandardButton")

for _name in ("AcceptRole", "ActionRole", "RejectRole"):
    _alias_enum(QDialogButtonBox, _name, "ButtonRole")

for _name in ("Cancel", "Close", "Ok", "Retry"):
    _alias_enum(QMessageBox, _name, "StandardButton")

for _name in ("Critical", "Information", "Question", "Warning"):
    _alias_enum(QMessageBox, _name, "Icon")

_alias_enum(QMessageBox, "ActionRole", "ButtonRole")
_alias_enum(QComboBox, "AdjustToMinimumContentsLengthWithIcon", "SizeAdjustPolicy")
_alias_enum(QDialog, "Accepted", "DialogCode")
_alias_enum(QDialog, "Rejected", "DialogCode")
_alias_enum(QLineEdit, "Password", "EchoMode")
_alias_enum(QPalette, "Window", "ColorRole")

_alias_qt("AlignCenter", "AlignmentFlag")
_alias_qt("AlignLeft", "AlignmentFlag")
_alias_qt("AlignRight", "AlignmentFlag")
_alias_qt("BottomDockWidgetArea", "DockWidgetArea")
_alias_qt("ItemIsEnabled", "ItemFlag")
_alias_qt("KeepAspectRatio", "AspectRatioMode")
_alias_qt("LeftDockWidgetArea", "DockWidgetArea")
_alias_qt("RichText", "TextFormat")
_alias_qt("RightDockWidgetArea", "DockWidgetArea")
_alias_qt("SmoothTransformation", "TransformationMode")
_alias_qt("SolidPattern", "BrushStyle")
_alias_qt("TopDockWidgetArea", "DockWidgetArea")
_alias_qt("UserRole", "ItemDataRole")
_alias_qt("WA_StyledBackground", "WidgetAttribute")

_alias_enum(QAbstractItemView, "NoEditTriggers", "EditTrigger")
_alias_enum(QAbstractItemView, "MultiSelection", "SelectionMode")
_alias_value(QListWidget, "MultiSelection", getattr(QAbstractItemView, "MultiSelection", None))


def exec_dialog(dialog):
    exec_method = getattr(dialog, "exec", None)
    if callable(exec_method):
        return exec_method()
    return dialog.exec_()


def exec_application(app):
    exec_method = getattr(app, "exec", None)
    if callable(exec_method):
        return exec_method()
    return app.exec_()
