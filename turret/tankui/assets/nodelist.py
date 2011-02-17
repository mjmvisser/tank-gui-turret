from PyQt4 import QtCore, QtGui

from model import SortFilterAssetsModel, AssetsModel, Filters

class CheckableProxyModel(QtGui.QSortFilterProxyModel): #IGNORE:R0904
    def __init__(self, parent, **kwargs):
        self._checkedIndexes = set()
        super(CheckableProxyModel, self).__init__(parent, **kwargs)

    def checkedIndexes(self):
        return self._checkedIndexes
    def setCheckedIndexes(self, indexes):
        self.beginResetModel()
        self._checkedIndexes = indexes
        self.endResetModel()

    def flags(self, index):
        flags = super(CheckableProxyModel, self).flags(index)
        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return QtCore.QVariant(QtCore.Qt.Checked if index in self._checkedIndexes else QtCore.Qt.Unchecked)
        else:
            return super(CheckableProxyModel, self).data(index, role)

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            state = value.toInt()[0]
            if state == QtCore.Qt.Checked:
                self._checkedIndexes.add(index)
            else:
                self._checkedIndexes.discard(index)
            self.dataChanged.emit(index, index)
            return True
        else:
            return super(CheckableProxyModel, self).setData(index, value, role)

    def setAllChecked(self, parent=QtCore.QModelIndex()):
        for row in range(0, self.rowCount(parent)):
            index = self.index(row, 0, parent)
            self.setData(index, QtCore.QVariant(QtCore.Qt.Checked), QtCore.Qt.CheckStateRole)
            self.setAllChecked(index)


class NodeListView(QtGui.QTreeView):
    def __init__(self, parent, **kwargs):
        super(NodeListView, self).__init__(parent, **kwargs)

        self._model = AssetsModel(self.viewport())
        self._sortFilterProxyModel = SortFilterAssetsModel(self.viewport())
        self._sortFilterProxyModel.setSourceModel(self._model)
        self._sortFilterProxyModel.setTypeFilter(Filters.Working)
        self._checkableProxyModel = CheckableProxyModel(self.viewport())
        self._checkableProxyModel.setSourceModel(self._sortFilterProxyModel)
        self._checkableProxyModel.dataChanged.connect(self._dataChanged)
        self.setModel(self._checkableProxyModel)


    def root(self):
        return self._model.root()
    def setRoot(self, root):
        self._model.setRoot(root)
        self.expand(self.model().index(0, 0))

    def setAllChecked(self):
        self._checkableProxyModel.setAllChecked()

    def checkedNodes(self):
        return set(index.data(QtCore.Qt.UserRole).toPyObject() for index in self._checkableProxyModel.checkedIndexes())

    checkedNodesChanged = QtCore.pyqtSignal(set)

    @QtCore.pyqtSlot()
    def _dataChanged(self):
        self.checkedNodesChanged.emit(self.checkedNodes())