from PyQt4 import QtCore, QtGui

class FileFilterView(QtGui.QColumnView):
    ##
    ## Signals
    ##
    filterChanged = QtCore.pyqtSignal(list)

    def __init__(self, parent=None, **kwargs):
        super(FileFilterView, self).__init__(parent, **kwargs)

        self.setModel(QtGui.QFileSystemModel(self))
