# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form - Copy.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QStatusBar, QTabWidget,
    QTextEdit, QTreeView, QVBoxLayout, QWidget)

class Ui_UIForm(object):
    def setupUi(self, UIForm):
        if not UIForm.objectName():
            UIForm.setObjectName(u"UIForm")
        UIForm.resize(826, 971)
        self.actionUser = QAction(UIForm)
        self.actionUser.setObjectName(u"actionUser")
        self.actionTerms = QAction(UIForm)
        self.actionTerms.setObjectName(u"actionTerms")
        self.actionPaths = QAction(UIForm)
        self.actionPaths.setObjectName(u"actionPaths")
        self.actionLimit = QAction(UIForm)
        self.actionLimit.setObjectName(u"actionLimit")
        self.centralwidget = QWidget(UIForm)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.filterLayout = QHBoxLayout()
        self.filterLayout.setObjectName(u"filterLayout")
        self.lblFilter = QLabel(self.centralwidget)
        self.lblFilter.setObjectName(u"lblFilter")

        self.filterLayout.addWidget(self.lblFilter)

        self.txtFilter = QLineEdit(self.centralwidget)
        self.txtFilter.setObjectName(u"txtFilter")

        self.filterLayout.addWidget(self.txtFilter)

        self.load_datasetsButton = QPushButton(self.centralwidget)
        self.load_datasetsButton.setObjectName(u"load_datasetsButton")

        self.filterLayout.addWidget(self.load_datasetsButton)


        self.verticalLayout.addLayout(self.filterLayout)

        self.datasetLayout = QHBoxLayout()
        self.datasetLayout.setObjectName(u"datasetLayout")
        self.datasetComboBox = QComboBox(self.centralwidget)
        self.datasetComboBox.setObjectName(u"datasetComboBox")

        self.datasetLayout.addWidget(self.datasetComboBox)

        self.labelCount = QLabel(self.centralwidget)
        self.labelCount.setObjectName(u"labelCount")
        self.labelCount.setMaximumSize(QSize(130, 16777215))

        self.datasetLayout.addWidget(self.labelCount)

        self.dataCatalogButton = QPushButton(self.centralwidget)
        self.dataCatalogButton.setObjectName(u"dataCatalogButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dataCatalogButton.sizePolicy().hasHeightForWidth())
        self.dataCatalogButton.setSizePolicy(sizePolicy)

        self.datasetLayout.addWidget(self.dataCatalogButton)


        self.verticalLayout.addLayout(self.datasetLayout)

        self.dataset_layout = QHBoxLayout()
        self.dataset_layout.setObjectName(u"dataset_layout")
        self.imageLabel = QLabel(self.centralwidget)
        self.imageLabel.setObjectName(u"imageLabel")
        self.imageLabel.setMinimumSize(QSize(192, 192))
        self.imageLabel.setMaximumSize(QSize(192, 192))
        self.imageLabel.setScaledContents(True)

        self.dataset_layout.addWidget(self.imageLabel)

        self.datasetDetails = QTextEdit(self.centralwidget)
        self.datasetDetails.setObjectName(u"datasetDetails")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.datasetDetails.sizePolicy().hasHeightForWidth())
        self.datasetDetails.setSizePolicy(sizePolicy1)

        self.dataset_layout.addWidget(self.datasetDetails)


        self.verticalLayout.addLayout(self.dataset_layout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab1 = QWidget()
        self.tab1.setObjectName(u"tab1")
        self.tab1Layout = QVBoxLayout(self.tab1)
        self.tab1Layout.setObjectName(u"tab1Layout")
        self.queryButtonLayout = QHBoxLayout()
        self.queryButtonLayout.setObjectName(u"queryButtonLayout")
        self.viewQueryButton = QPushButton(self.tab1)
        self.viewQueryButton.setObjectName(u"viewQueryButton")

        self.queryButtonLayout.addWidget(self.viewQueryButton)


        self.tab1Layout.addLayout(self.queryButtonLayout)

        self.splitterQueryForm = QSplitter(self.tab1)
        self.splitterQueryForm.setObjectName(u"splitterQueryForm")
        self.splitterQueryForm.setOrientation(Qt.Vertical)
        self.scrollArea = QScrollArea(self.splitterQueryForm)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(30)
        sizePolicy2.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy2)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setBaseSize(QSize(0, 0))
        self.scrollArea.setWidgetResizable(True)
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName(u"scrollWidget")
        self.scrollWidget.setGeometry(QRect(0, 0, 782, 252))
        self.formLayout = QVBoxLayout(self.scrollWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.scrollArea.setWidget(self.scrollWidget)
        self.splitterQueryForm.addWidget(self.scrollArea)
        self.searchControlsWrapper = QWidget(self.splitterQueryForm)
        self.searchControlsWrapper.setObjectName(u"searchControlsWrapper")
        self.vboxLayout = QVBoxLayout(self.searchControlsWrapper)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(0, 0, 0, 0)
        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.requestDataButton = QPushButton(self.searchControlsWrapper)
        self.requestDataButton.setObjectName(u"requestDataButton")

        self.hboxLayout.addWidget(self.requestDataButton)

        self.labelLimit = QLabel(self.searchControlsWrapper)
        self.labelLimit.setObjectName(u"labelLimit")

        self.hboxLayout.addWidget(self.labelLimit)

        self.limitLineEdit = QLineEdit(self.searchControlsWrapper)
        self.limitLineEdit.setObjectName(u"limitLineEdit")
        sizePolicy.setHeightForWidth(self.limitLineEdit.sizePolicy().hasHeightForWidth())
        self.limitLineEdit.setSizePolicy(sizePolicy)

        self.hboxLayout.addWidget(self.limitLineEdit)

        self.labelDescription = QLabel(self.searchControlsWrapper)
        self.labelDescription.setObjectName(u"labelDescription")

        self.hboxLayout.addWidget(self.labelDescription)

        self.showRequestButton = QPushButton(self.searchControlsWrapper)
        self.showRequestButton.setObjectName(u"showRequestButton")

        self.hboxLayout.addWidget(self.showRequestButton)


        self.vboxLayout.addLayout(self.hboxLayout)

        self.fileListWidget = QListWidget(self.searchControlsWrapper)
        self.fileListWidget.setObjectName(u"fileListWidget")
        self.fileListWidget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.vboxLayout.addWidget(self.fileListWidget)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.selectAllButton = QPushButton(self.searchControlsWrapper)
        self.selectAllButton.setObjectName(u"selectAllButton")
        self.selectAllButton.setMinimumSize(QSize(100, 0))
        self.selectAllButton.setMaximumSize(QSize(100, 16777215))

        self.buttonLayout.addWidget(self.selectAllButton)

        self.clearAllButton = QPushButton(self.searchControlsWrapper)
        self.clearAllButton.setObjectName(u"clearAllButton")
        self.clearAllButton.setMinimumSize(QSize(120, 0))
        self.clearAllButton.setMaximumSize(QSize(120, 16777215))

        self.buttonLayout.addWidget(self.clearAllButton)

        self.downloadButton = QPushButton(self.searchControlsWrapper)
        self.downloadButton.setObjectName(u"downloadButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.downloadButton.sizePolicy().hasHeightForWidth())
        self.downloadButton.setSizePolicy(sizePolicy3)
        self.downloadButton.setMaximumSize(QSize(150, 16777215))

        self.buttonLayout.addWidget(self.downloadButton)

        self.btn_download_location = QPushButton(self.searchControlsWrapper)
        self.btn_download_location.setObjectName(u"btn_download_location")
        self.btn_download_location.setMaximumSize(QSize(175, 16777215))

        self.buttonLayout.addWidget(self.btn_download_location)

        self.btn_open_file_location = QPushButton(self.searchControlsWrapper)
        self.btn_open_file_location.setObjectName(u"btn_open_file_location")
        self.btn_open_file_location.setMaximumSize(QSize(175, 16777215))

        self.buttonLayout.addWidget(self.btn_open_file_location)

        self.cancelButton = QPushButton(self.searchControlsWrapper)
        self.cancelButton.setObjectName(u"cancelButton")
        self.cancelButton.setMaximumSize(QSize(80, 16777215))

        self.buttonLayout.addWidget(self.cancelButton)


        self.vboxLayout.addLayout(self.buttonLayout)

        self.progressBar = QProgressBar(self.searchControlsWrapper)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.vboxLayout.addWidget(self.progressBar)

        self.statusLabel = QLabel(self.searchControlsWrapper)
        self.statusLabel.setObjectName(u"statusLabel")

        self.vboxLayout.addWidget(self.statusLabel)

        self.splitterQueryForm.addWidget(self.searchControlsWrapper)

        self.tab1Layout.addWidget(self.splitterQueryForm)

        self.tabWidget.addTab(self.tab1, "")
        self.tab2 = QWidget()
        self.tab2.setObjectName(u"tab2")
        self.tab2Layout = QVBoxLayout(self.tab2)
        self.tab2Layout.setObjectName(u"tab2Layout")
        self.layerSelectionLayout = QHBoxLayout()
        self.layerSelectionLayout.setObjectName(u"layerSelectionLayout")
        self.comboBoxLayout = QVBoxLayout()
        self.comboBoxLayout.setObjectName(u"comboBoxLayout")
        self.hboxLayout1 = QHBoxLayout()
        self.hboxLayout1.setObjectName(u"hboxLayout1")
        self.labelSearchWMS = QLabel(self.tab2)
        self.labelSearchWMS.setObjectName(u"labelSearchWMS")

        self.hboxLayout1.addWidget(self.labelSearchWMS)

        self.txtSearchWMS = QLineEdit(self.tab2)
        self.txtSearchWMS.setObjectName(u"txtSearchWMS")

        self.hboxLayout1.addWidget(self.txtSearchWMS)


        self.comboBoxLayout.addLayout(self.hboxLayout1)

        self.splitterWMS = QSplitter(self.tab2)
        self.splitterWMS.setObjectName(u"splitterWMS")
        self.splitterWMS.setOrientation(Qt.Vertical)
        self.treeViewWMS = QTreeView(self.splitterWMS)
        self.treeViewWMS.setObjectName(u"treeViewWMS")
        self.splitterWMS.addWidget(self.treeViewWMS)
        self.txt_info = QPlainTextEdit(self.splitterWMS)
        self.txt_info.setObjectName(u"txt_info")
        self.txt_info.setReadOnly(True)
        self.splitterWMS.addWidget(self.txt_info)

        self.comboBoxLayout.addWidget(self.splitterWMS)


        self.layerSelectionLayout.addLayout(self.comboBoxLayout)


        self.tab2Layout.addLayout(self.layerSelectionLayout)

        self.addToLayersButton = QPushButton(self.tab2)
        self.addToLayersButton.setObjectName(u"addToLayersButton")

        self.tab2Layout.addWidget(self.addToLayersButton)

        self.tabWidget.addTab(self.tab2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        UIForm.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(UIForm)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 826, 21))
        self.menuSettings = QMenu(self.menuBar)
        self.menuSettings.setObjectName(u"menuSettings")
        UIForm.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(UIForm)
        self.statusBar.setObjectName(u"statusBar")
        UIForm.setStatusBar(self.statusBar)

        self.menuBar.addAction(self.menuSettings.menuAction())
        self.menuSettings.addAction(self.actionUser)
        self.menuSettings.addAction(self.actionTerms)
        self.menuSettings.addAction(self.actionPaths)
        self.menuSettings.addAction(self.actionLimit)

        self.retranslateUi(UIForm)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(UIForm)
    # setupUi

    def retranslateUi(self, UIForm):
        self.actionUser.setText(QCoreApplication.translate("UIForm", u"User", None))
        self.actionTerms.setText(QCoreApplication.translate("UIForm", u"Terms and Conditions", None))
        self.actionPaths.setText(QCoreApplication.translate("UIForm", u"Paths", None))
        self.actionLimit.setText(QCoreApplication.translate("UIForm", u"Set limit in search", None))
        self.lblFilter.setText(QCoreApplication.translate("UIForm", u"Filter:", None))
        self.txtFilter.setPlaceholderText(QCoreApplication.translate("UIForm", u"e.g. snow+cover (AND), snow|cover (OR), \"snow cover\" (phrase)", None))
        self.load_datasetsButton.setText(QCoreApplication.translate("UIForm", u"Update", None))
        self.labelCount.setText(QCoreApplication.translate("UIForm", u"Number ----  of ---- ", None))
        self.dataCatalogButton.setText(QCoreApplication.translate("UIForm", u"Data Catalog", None))
        self.viewQueryButton.setText(QCoreApplication.translate("UIForm", u"Show query parameters", None))
        self.requestDataButton.setText(QCoreApplication.translate("UIForm", u"Request Data", None))
        self.labelLimit.setText(QCoreApplication.translate("UIForm", u"Limit (cutoff)", None))
        self.labelDescription.setText(QCoreApplication.translate("UIForm", u"The maximum number of results to return. Set to 0 to return all results", None))
        self.showRequestButton.setText(QCoreApplication.translate("UIForm", u"Show API REquest(s)", None))
        self.selectAllButton.setText(QCoreApplication.translate("UIForm", u"Select All", None))
        self.clearAllButton.setText(QCoreApplication.translate("UIForm", u"Deselect All", None))
        self.downloadButton.setText(QCoreApplication.translate("UIForm", u"Download", None))
        self.btn_download_location.setText(QCoreApplication.translate("UIForm", u"Choose Folder", None))
        self.btn_open_file_location.setText(QCoreApplication.translate("UIForm", u"Open Folder", None))
        self.cancelButton.setText(QCoreApplication.translate("UIForm", u"Cancel", None))
        self.statusLabel.setText(QCoreApplication.translate("UIForm", u"Status: Klar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab1), QCoreApplication.translate("UIForm", u"Datasets", None))
        self.labelSearchWMS.setText(QCoreApplication.translate("UIForm", u"Filter layers (highlight in text)", None))
        self.addToLayersButton.setText(QCoreApplication.translate("UIForm", u"Add to Layers", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab2), QCoreApplication.translate("UIForm", u"WMS/WMTS", None))
        self.menuSettings.setTitle(QCoreApplication.translate("UIForm", u"Settings", None))
        pass
    # retranslateUi

