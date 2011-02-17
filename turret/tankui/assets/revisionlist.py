from PyQt4 import QtCore, QtGui

from .ui_revisionlist import Ui_RevisionListDialog

class RevisionListModel(QtCore.QAbstractListModel):
    def __init__(self, parent, **kwargs):
        self._revisions = ()
        self._checkState = ()
        super(RevisionListModel, self).__init__(parent, **kwargs)

    def checkedRevisions(self):
        return [r for r, c in zip(self._revisions, self._checkState) if c == QtCore.Qt.Checked]
    def revisions(self):
        return self._revisions
    def setRevisions(self, revisions):
        self.beginResetModel()
        self._revisions = revisions
        self._checkState = [QtCore.Qt.Unchecked]*len(revisions)
        self.endResetModel()

    def rowCount(self, parent):
        return len(self._revisions)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        assert orientation == QtCore.Qt.Horizontal
        if role == QtCore.Qt.DisplayRole and section == 0:
            return "Revision"
        else:
            return super(RevisionListModel, self).headerData(section, orientation, role)

    def flags(self, index):
        flags = super(RevisionListModel, self).flags(index)
        flags |= QtCore.Qt.ItemIsUserCheckable
        flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return str(self._revisions[index.row()])
        elif role == QtCore.Qt.CheckStateRole:
            return self._checkState[index.row()]

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        changed = False

        if role == QtCore.Qt.CheckStateRole:
            self._checkState[index.row()] = value.toInt()[0]
            changed = True

        if changed:
            self.dataChanged.emit(index, index)

        return changed

class RevisionListView(QtGui.QListView):
    def __init__(self, parent, **kwargs):
        super(RevisionListView, self).__init__(parent, **kwargs)

        self._model = RevisionListModel(self)
        self.setModel(self._model)

        self._model.dataChanged.connect(self._dataChanged)

    revisionsChanged = QtCore.pyqtSignal(list)

    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def _dataChanged(self, topLeft, bottomRight):
        self.revisionChanged.emit(self.revisions())

    def revisions(self):
        return self._model.checkedRevisions()
    def setRevisions(self, revisions):
        self._model.setRevisions(revisions)


class RevisionListDialog(QtGui.QDialog, Ui_RevisionListDialog):
    def __init__(self, parent=None, **kwargs):
        if parent is not None:
            super(RevisionListDialog, self).__init__(parent, **kwargs)
        else:
            super(RevisionListDialog, self).__init__(**kwargs)

        self.setupUi(self)

        self._model = RevisionListModel(self._revisionListView)
        self._revisionListView.setModel(self._model)

    def revisions(self):
        return self._model.checkedRevisions()
    def setRevisions(self, revisions):
        self._model.setRevisions(revisions)
