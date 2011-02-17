from PyQt4 import QtCore, QtGui

class LineEdit(QtGui.QLineEdit):
    """A line edit with a clear button."""
    def __init__(self, parent, **kwargs):
        super(LineEdit, self).__init__(parent, **kwargs)

        self._clearButton = QtGui.QToolButton(self)

        icon = self.style().standardIcon(QtGui.QStyle.SP_TitleBarCloseButton)

        self._clearButton.setIcon(icon)
        self._clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self._clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self._clearButton.hide()

        self._clearButton.clicked.connect(self._clearText)
        self.textChanged.connect(self._updateCloseButton)

        frame_width = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)

        self.setStyleSheet("QLineEdit { padding-right: %dpx; } " % (self._clearButton.sizeHint().width() + frame_width + 1))

        msz = self.minimumSizeHint()

        self.setMinimumSize(max(msz.width(), self._clearButton.sizeHint().height() + frame_width * 2 + 2),
                            max(msz.height(), self._clearButton.sizeHint().height() + frame_width * 2 + 2))

    def resizeEvent(self, event):
        sz = self._clearButton.sizeHint()
        frame_width = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self._clearButton.move((self.rect().right() - frame_width - sz.width()),
                               (self.rect().bottom() + 1 - sz.height())/2)

    def _clearText(self):
        self.clear()
        self.returnPressed.emit()

    def _updateCloseButton(self, text):
        self._clearButton.setVisible(not text.isEmpty())

if __name__ == "__main__":
    app = QtGui.QApplication([])
    le = LineEdit(None)
    le.show()
    app.exec_()