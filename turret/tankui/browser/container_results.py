from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..utils import pyqtOverrideCursor

import tank

class ContainerResultsModel(QAbstractItemModel):
    ContainerColumn = 0
    
    def __init__(self, parent, **kwargs):
        super(ContainerResultsModel, self).__init__(parent, **kwargs)
        self._result_sets = []
        self._results = []
        
    @pyqtOverrideCursor(Qt.BusyCursor)
    def setResultSets(self, result_sets):
        self.beginResetModel()
        self._result_sets = result_sets
        self._results = []
        self.endResetModel()
        
    def columnCount(self, parent=QModelIndex()):
        assert parent == QModelIndex()
        return 1

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._results)
        else:
            return 0
        
    def canFetchMore(self, parent):
        return len(self._result_sets) > 0

    def fetchMore(self, parent):
        assert len(self._result_sets) > 0
        while len(self._result_sets) > 0:
            # keep fetching until we get something, or exhaust the result sets
            rs = self._result_sets.pop(0)
            new_results = rs.fetch_all()
            if len(new_results) != 0:
                row_count = self.rowCount(parent)
                self.beginInsertRows(parent, row_count, row_count+len(new_results)-1)
                self._results.extend(new_results)
                self.endInsertRows()
                break

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if section == ContainerResultsModel.ContainerColumn:
                return "Container"

        return None
        
    def flags(self, index):
        result = super(ContainerResultsModel, self).flags(index)
        #result |= Qt.ItemIsUserCheckable
        return result
        
    def data(self, index, role=Qt.DisplayRole):
        if index == QModelIndex():
            result = None
        else:
            obj = index.internalPointer()
            column = index.column()
            if role == Qt.DisplayRole:
                if column == ContainerResultsModel.ContainerColumn:
                    result = str(obj)
                else:
                    result = None
            elif role == Qt.UserRole:
                result = index.internalPointer()
            else:
                result = None
                
        return QVariant(result)
    
#    def setData(self, index, value, role=Qt.DisplayRole):
#        if index != QModelIndex():
#            obj = index.internalPointer()
#            if role == Qt.CheckStateRole:
#                if value.toInt()[0] == Qt.Checked:
#                    self._checked.add(obj)
#                else:
#                    self._checked.remove(obj)
#                return True
#        return False

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        else:
            return self.createIndex(row, column, self._results[row])

    def parent(self, parent):
        return QModelIndex()


class ContainerResultsView(QTreeView):
    def __init__(self, parent, **kwargs):
        super(ContainerResultsView, self).__init__(parent, **kwargs)
        self._worker = None

        # create and set a new model
        model = ContainerResultsModel(self)
        model.rowsInserted.connect(self._resizeColumns)
        self.setModel(model)

    def setFilter(self, value):
        self._filter = value
        self.model().setFilter(value)

    def _cleanUpWorker(self, worker):
        del worker
        
    @pyqtSlot(list)
    def setConstraints(self, constraints):
        if self._worker is not None:
            # clean it up five seconds in the future
            QTimer.singleShot(5000, lambda worker=self._worker: self._cleanUpWorker(worker))

        if len(constraints) > 0:
            QApplication.setOverrideCursor(Qt.BusyCursor)
            self._worker = ContainerQueryWorker(constraints)
            self._worker.output.connect(self._setResultSets)
            self._worker.start()
        else:
            self._worker = None
            self.model().setResultSets([])

    def _setResultSets(self, result_sets):
        self.model().setResultSets(result_sets)
        QApplication.restoreOverrideCursor()        

    def _resizeColumns(self):
        for column in range(0, self.model().columnCount()):
            self.resizeColumnToContents(column)

    def select(self, obj):
        if self.selectionModel() is None:
            return
        
        self.selectionModel().clear()
        for index in self.model().match(QModelIndex(), Qt.UserRole, obj, 1, Qt.MatchExactly):
            self.selectionModel().select(index, QItemSelectionModel.Select)

class ContainerQueryWorker(QThread):
    def __init__(self, constraints):
        super(ContainerQueryWorker, self).__init__()
        self._objs = constraints
        self.stopped = False

    output = pyqtSignal(list)
    
    def __del__(self):
        self.stopped = True
        while self.isRunning():
            self.wait()

    def run(self):
        assert len(self._objs) > 0
        constraints = []
        # add label constraints
        constraints += ["labels contains %s" % l for l in self._objs if isinstance(l, tank.TankLabel)]
        
        # get container types
        container_types = [ct for ct in self._objs if isinstance(ct, tank.TankType) and ct.properties.container_type == tank.constants.ContainerType.CONTAINER]

        # default to all container types if none are specified
        if len(container_types) == 0:
            # FIXME: ContainerGlobals search currently returns system containers as well (#12103)
            #container_types = ["ContainerGlobals"]
            container_types = tank.list_container_types()

        # find all revisions that match
        result_sets = []
        if len(constraints) > 0: 
            for ct in container_types:
                if self.stopped:
                    return
                result_sets.append(tank.get_children(ct, constraints))

        # send the output signal with the results
        if not self.stopped:
            self.output.emit(result_sets)
