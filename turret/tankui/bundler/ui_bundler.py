# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bundler.ui'
#
# Created: Wed Dec  1 17:57:36 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_BundlerWindow(object):
    def setupUi(self, BundlerWindow):
        BundlerWindow.setObjectName(_fromUtf8("BundlerWindow"))
        BundlerWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(BundlerWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self._assetsWindow = AssetsWindow(self.centralwidget)
        self._assetsWindow.setObjectName(_fromUtf8("_assetsWindow"))
        self.verticalLayout.addWidget(self._assetsWindow)
        BundlerWindow.setCentralWidget(self.centralwidget)
        self._menuBar = QtGui.QMenuBar(BundlerWindow)
        self._menuBar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self._menuBar.setObjectName(_fromUtf8("_menuBar"))
        self._tankMenu = QtGui.QMenu(self._menuBar)
        self._tankMenu.setObjectName(_fromUtf8("_tankMenu"))
        BundlerWindow.setMenuBar(self._menuBar)
        self._setProjectAction = QtGui.QAction(BundlerWindow)
        self._setProjectAction.setObjectName(_fromUtf8("_setProjectAction"))
        self._openBundleAction = QtGui.QAction(BundlerWindow)
        self._openBundleAction.setObjectName(_fromUtf8("_openBundleAction"))
        self._quitAction = QtGui.QAction(BundlerWindow)
        self._quitAction.setObjectName(_fromUtf8("_quitAction"))
        self._newBundleAction = QtGui.QAction(BundlerWindow)
        self._newBundleAction.setObjectName(_fromUtf8("_newBundleAction"))
        self._saveBundleAction = QtGui.QAction(BundlerWindow)
        self._saveBundleAction.setObjectName(_fromUtf8("_saveBundleAction"))
        self._saveBundleAsAction = QtGui.QAction(BundlerWindow)
        self._saveBundleAsAction.setObjectName(_fromUtf8("_saveBundleAsAction"))
        self._tankMenu.addAction(self._newBundleAction)
        self._tankMenu.addAction(self._openBundleAction)
        self._tankMenu.addAction(self._saveBundleAction)
        self._tankMenu.addAction(self._saveBundleAsAction)
        self._tankMenu.addSeparator()
        self._tankMenu.addAction(self._setProjectAction)
        self._tankMenu.addSeparator()
        self._tankMenu.addAction(self._quitAction)
        self._menuBar.addAction(self._tankMenu.menuAction())

        self.retranslateUi(BundlerWindow)
        QtCore.QObject.connect(self._quitAction, QtCore.SIGNAL(_fromUtf8("activated()")), BundlerWindow.close)
        QtCore.QMetaObject.connectSlotsByName(BundlerWindow)

    def retranslateUi(self, BundlerWindow):
        BundlerWindow.setWindowTitle(QtGui.QApplication.translate("BundlerWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self._tankMenu.setTitle(QtGui.QApplication.translate("BundlerWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self._setProjectAction.setText(QtGui.QApplication.translate("BundlerWindow", "&Set Project...", None, QtGui.QApplication.UnicodeUTF8))
        self._openBundleAction.setText(QtGui.QApplication.translate("BundlerWindow", "&Open...", None, QtGui.QApplication.UnicodeUTF8))
        self._quitAction.setText(QtGui.QApplication.translate("BundlerWindow", "&Quit", None, QtGui.QApplication.UnicodeUTF8))
        self._newBundleAction.setText(QtGui.QApplication.translate("BundlerWindow", "&New", None, QtGui.QApplication.UnicodeUTF8))
        self._saveBundleAction.setText(QtGui.QApplication.translate("BundlerWindow", "&Save", None, QtGui.QApplication.UnicodeUTF8))
        self._saveBundleAsAction.setText(QtGui.QApplication.translate("BundlerWindow", "Save &As...", None, QtGui.QApplication.UnicodeUTF8))

from ..assets import AssetsWindow
