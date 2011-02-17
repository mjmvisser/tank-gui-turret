# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'revisionlist.ui'
#
# Created: Mon Nov  8 17:10:16 2010
#      by: PyQt4 UI code generator 4.7
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_RevisionListDialog(object):
    def setupUi(self, RevisionListDialog):
        RevisionListDialog.setObjectName("RevisionListDialog")
        RevisionListDialog.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(RevisionListDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self._revisionListView = QtGui.QListView(RevisionListDialog)
        self._revisionListView.setAlternatingRowColors(True)
        self._revisionListView.setWordWrap(True)
        self._revisionListView.setObjectName("_revisionListView")
        self.verticalLayout.addWidget(self._revisionListView)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self._label = QtGui.QLabel(RevisionListDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setObjectName("_label")
        self.horizontalLayout.addWidget(self._label)
        self._buttons = QtGui.QDialogButtonBox(RevisionListDialog)
        self._buttons.setOrientation(QtCore.Qt.Horizontal)
        self._buttons.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self._buttons.setObjectName("_buttons")
        self.horizontalLayout.addWidget(self._buttons)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(RevisionListDialog)
        QtCore.QObject.connect(self._buttons, QtCore.SIGNAL("accepted()"), RevisionListDialog.accept)
        QtCore.QObject.connect(self._buttons, QtCore.SIGNAL("rejected()"), RevisionListDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(RevisionListDialog)
        RevisionListDialog.setTabOrder(self._revisionListView, self._buttons)

    def retranslateUi(self, RevisionListDialog):
        RevisionListDialog.setWindowTitle(QtGui.QApplication.translate("RevisionListDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))

