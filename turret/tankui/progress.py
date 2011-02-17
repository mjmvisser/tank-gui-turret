from PyQt4 import QtCore, QtGui

__all__ = ["ProgressDialog"]

class ProgressDialog(QtGui.QDialog):
    def __init__(self, delay=1000, parent=None):
        super(ProgressDialog, self).__init__(parent)

        layout = QtGui.QVBoxLayout()

        self._text = QtGui.QTextEdit()
        self._text.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self._text.setReadOnly(True)

        layout.addWidget(self._text)

        self._progress = QtGui.QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setValue(0)

        layout.addWidget(self._progress)

        self._progress.hide()

        self.setLayout(layout)

        # trigger an event in delay seconds
        self._showTimer = self.startTimer(delay)

    def timerEvent(self, event):
        if event.timerId() == self._showTimer:
            # show the window
            self.show()
            self.update()
            self.killTimer(self._showTimer)
            QtGui.qApp.processEvents()

    def close(self):
        self.killTimer(self._showTimer)
        super(ProgressDialog, self).close()

    def closeEvent(self, event):
        self.killTimer(self._showTimer)
        super(ProgressDialog, self).closeEvent(event)

    def sizeHint(self): #IGNORE:R0201
        return QtCore.QSize(800, 300)

    def on_publish(self, revision_type, container, filename):
        s = "(publish) %s to %s as %s" % (filename, container, revision_type)
        self._text.append(s + "\n")
        self._text.moveCursor(QtGui.QTextCursor.End)
        self._text.ensureCursorVisible()
        QtGui.qApp.processEvents()
        print s

    def on_progress_change(self, files_processed, total_files_to_process):
        self._progress.show()
        self._progress.setMaximum(total_files_to_process)
        self._progress.setValue(files_processed)
        QtGui.qApp.processEvents()

    def on_execute(self, action, revision_type, container, filename):
        s = "(%s) %s from %s from %s" % (action, revision_type, container, filename)
        self._text.append(s + "\n")
        self._text.moveCursor(QtGui.QTextCursor.End)
        self._text.ensureCursorVisible()
        QtGui.qApp.processEvents()
        print s
