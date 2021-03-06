# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'assets.ui'
#
# Created: Thu Nov 25 15:34:57 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_AssetsWindow(object):
    def setupUi(self, AssetsWindow):
        AssetsWindow.setObjectName(_fromUtf8("AssetsWindow"))
        AssetsWindow.resize(911, 579)
        self.verticalLayout_3 = QtGui.QVBoxLayout(AssetsWindow)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label = QtGui.QLabel(AssetsWindow)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_3.addWidget(self.label)
        self._filterAll = QtGui.QToolButton(AssetsWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/filter_all.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._filterAll.setIcon(icon)
        self._filterAll.setCheckable(True)
        self._filterAll.setChecked(True)
        self._filterAll.setAutoExclusive(True)
        self._filterAll.setObjectName(_fromUtf8("_filterAll"))
        self.horizontalLayout_3.addWidget(self._filterAll)
        self._filterWorking = QtGui.QToolButton(AssetsWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/filter_working.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._filterWorking.setIcon(icon1)
        self._filterWorking.setCheckable(True)
        self._filterWorking.setAutoExclusive(True)
        self._filterWorking.setObjectName(_fromUtf8("_filterWorking"))
        self.horizontalLayout_3.addWidget(self._filterWorking)
        self._filterRevision = QtGui.QToolButton(AssetsWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/filter_revisions.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._filterRevision.setIcon(icon2)
        self._filterRevision.setCheckable(True)
        self._filterRevision.setAutoExclusive(True)
        self._filterRevision.setObjectName(_fromUtf8("_filterRevision"))
        self.horizontalLayout_3.addWidget(self._filterRevision)
        self._filterOther = QtGui.QToolButton(AssetsWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/filter_other.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._filterOther.setIcon(icon3)
        self._filterOther.setCheckable(True)
        self._filterOther.setAutoExclusive(True)
        self._filterOther.setObjectName(_fromUtf8("_filterOther"))
        self.horizontalLayout_3.addWidget(self._filterOther)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self._searchBox = LineEdit(AssetsWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._searchBox.sizePolicy().hasHeightForWidth())
        self._searchBox.setSizePolicy(sizePolicy)
        self._searchBox.setObjectName(_fromUtf8("_searchBox"))
        self.horizontalLayout_3.addWidget(self._searchBox)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.line = QtGui.QFrame(AssetsWindow)
        self.line.setFrameShadow(QtGui.QFrame.Plain)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.verticalLayout_3.addWidget(self.line)
        self.splitter = QtGui.QSplitter(AssetsWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self._view = AssetsView(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._view.sizePolicy().hasHeightForWidth())
        self._view.setSizePolicy(sizePolicy)
        self._view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self._view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self._view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._view.setSortingEnabled(True)
        self._view.setObjectName(_fromUtf8("_view"))
        self.verticalLayout.addWidget(self._view)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self._addButton = QtGui.QToolButton(self.layoutWidget)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/plus.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._addButton.setIcon(icon4)
        self._addButton.setObjectName(_fromUtf8("_addButton"))
        self.horizontalLayout.addWidget(self._addButton)
        self._removeButton = QtGui.QToolButton(self.layoutWidget)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/minus.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._removeButton.setIcon(icon5)
        self._removeButton.setObjectName(_fromUtf8("_removeButton"))
        self.horizontalLayout.addWidget(self._removeButton)
        self._gearButton = QtGui.QToolButton(self.layoutWidget)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/gear.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._gearButton.setIcon(icon6)
        self._gearButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        self._gearButton.setObjectName(_fromUtf8("_gearButton"))
        self.horizontalLayout.addWidget(self._gearButton)
        spacerItem1 = QtGui.QSpacerItem(138, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self._refreshButton = QtGui.QToolButton(self.layoutWidget)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/refresh.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self._refreshButton.setIcon(icon7)
        self._refreshButton.setObjectName(_fromUtf8("_refreshButton"))
        self.horizontalLayout.addWidget(self._refreshButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.layoutWidget1 = QtGui.QWidget(self.splitter)
        self.layoutWidget1.setObjectName(_fromUtf8("layoutWidget1"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self._inspector = InspectorView(self.layoutWidget1)
        self._inspector.setObjectName(_fromUtf8("_inspector"))
        self.verticalLayout_2.addWidget(self._inspector)
        self.verticalLayout_3.addWidget(self.splitter)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem2 = QtGui.QSpacerItem(388, 17, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self._buttons = QtGui.QDialogButtonBox(AssetsWindow)
        self._buttons.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Close)
        self._buttons.setObjectName(_fromUtf8("_buttons"))
        self.horizontalLayout_2.addWidget(self._buttons)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.retranslateUi(AssetsWindow)
        QtCore.QObject.connect(self._addButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AssetsWindow.add)
        QtCore.QObject.connect(self._removeButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AssetsWindow.removeSelected)
        QtCore.QObject.connect(self._refreshButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AssetsWindow.refresh)
        QtCore.QObject.connect(self._buttons, QtCore.SIGNAL(_fromUtf8("clicked(QAbstractButton*)")), AssetsWindow.buttonPressed)
        QtCore.QObject.connect(self._view, QtCore.SIGNAL(_fromUtf8("selectionModified(QItemSelection,QItemSelection)")), self._inspector.update)
        QtCore.QMetaObject.connectSlotsByName(AssetsWindow)
        AssetsWindow.setTabOrder(self._view, self._addButton)
        AssetsWindow.setTabOrder(self._addButton, self._removeButton)
        AssetsWindow.setTabOrder(self._removeButton, self._gearButton)

    def retranslateUi(self, AssetsWindow):
        AssetsWindow.setWindowTitle(QtGui.QApplication.translate("AssetsWindow", "Assets", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("AssetsWindow", "Filter: ", None, QtGui.QApplication.UnicodeUTF8))
        self._filterAll.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Show all", None, QtGui.QApplication.UnicodeUTF8))
        self._filterAll.setText(QtGui.QApplication.translate("AssetsWindow", "All", None, QtGui.QApplication.UnicodeUTF8))
        self._filterWorking.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Show working", None, QtGui.QApplication.UnicodeUTF8))
        self._filterWorking.setText(QtGui.QApplication.translate("AssetsWindow", "Working", None, QtGui.QApplication.UnicodeUTF8))
        self._filterRevision.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Show revisions", None, QtGui.QApplication.UnicodeUTF8))
        self._filterRevision.setText(QtGui.QApplication.translate("AssetsWindow", "Revisions", None, QtGui.QApplication.UnicodeUTF8))
        self._filterOther.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Show others", None, QtGui.QApplication.UnicodeUTF8))
        self._filterOther.setText(QtGui.QApplication.translate("AssetsWindow", "Other", None, QtGui.QApplication.UnicodeUTF8))
        self._searchBox.setPlaceholderText(QtGui.QApplication.translate("AssetsWindow", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self._addButton.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Add revisions...", None, QtGui.QApplication.UnicodeUTF8))
        self._addButton.setText(QtGui.QApplication.translate("AssetsWindow", "...", None, QtGui.QApplication.UnicodeUTF8))
        self._removeButton.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Remove selected revisions", None, QtGui.QApplication.UnicodeUTF8))
        self._removeButton.setText(QtGui.QApplication.translate("AssetsWindow", "...", None, QtGui.QApplication.UnicodeUTF8))
        self._gearButton.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Actions...", None, QtGui.QApplication.UnicodeUTF8))
        self._gearButton.setText(QtGui.QApplication.translate("AssetsWindow", "...", None, QtGui.QApplication.UnicodeUTF8))
        self._refreshButton.setToolTip(QtGui.QApplication.translate("AssetsWindow", "Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self._refreshButton.setText(QtGui.QApplication.translate("AssetsWindow", "...", None, QtGui.QApplication.UnicodeUTF8))

from .view import AssetsView
from .inspector import InspectorView
from ..lineedit import LineEdit
import icons_rc
