from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..utils import pyqtOverrideCursor

import tank

class RevisionResultsModel(QAbstractItemModel):
    VersionColumn = 0
    RevisionTypeColumn = 1
    ContainerColumn = 2
    SealedAtColumn = 3
    CreatedByColumn = 4
    DescriptionColumn = 5
    
    def __init__(self, parent, **kwargs):
        super(RevisionResultsModel, self).__init__(parent, **kwargs)
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
        return 6

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._results)
        else:
            return 0
        
    def canFetchMore(self, parent):
        return len(self._result_sets) > 0

    def fetchMore(self, parent):
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
            if section == RevisionResultsModel.VersionColumn:
                return "Version"
            elif section == RevisionResultsModel.RevisionTypeColumn:
                return "Type"
            elif section == RevisionResultsModel.ContainerColumn:
                return "Container"
            elif section == RevisionResultsModel.SealedAtColumn:
                return "Sealed"
            elif section == RevisionResultsModel.CreatedByColumn:
                return "Created By"
            elif section == RevisionResultsModel.DescriptionColumn:
                return "Description"
            
        return None
        
    def flags(self, index):
        result = super(RevisionResultsModel, self).flags(index)
        #result |= Qt.ItemIsUserCheckable
        return result
        
    def data(self, index, role=Qt.DisplayRole):
        if index == QModelIndex():
            result = None
        else:
            obj = index.internalPointer()
            column = index.column()
            if role == Qt.DisplayRole:
                if column == RevisionResultsModel.VersionColumn:
                    result = obj.system.name
                elif column == RevisionResultsModel.RevisionTypeColumn:
                    result = obj.system.type_name
                elif column == RevisionResultsModel.ContainerColumn:
                    result = str(obj.container)
                elif column == RevisionResultsModel.SealedAtColumn:
                    result = tank.common.propertytypes.DateTimePropertyType.utc_to_local_str(obj.system.seal_date)
                elif column == RevisionResultsModel.CreatedByColumn:
                    try:
                        result = obj.properties.created_by.system.name
                    except AttributeError:
                        result = None
                elif column == RevisionResultsModel.DescriptionColumn:
                    result = obj.properties.description
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

class RevisionResultsProxyModel(QSortFilterProxyModel):
    FilterAll=0
    FilterLatest=1
    FilterRecommended=2

    def __init__(self, parent, **kwargs):
        self._filter = RevisionResultsProxyModel.FilterAll
        super(RevisionResultsProxyModel, self).__init__(parent, **kwargs)

    def filter(self):
        return self._filter
    def setFilter(self, value):
        self._filter = value
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if not index.isValid():
            return False
        else:
            obj = index.data(Qt.UserRole).toPyObject()
            
            # workaround until get_latest_versions is implemented in the server api
            obj = tank.find(str(obj))
 
            return (self._filter == RevisionResultsProxyModel.FilterAll) or \
                   (self._filter == RevisionResultsProxyModel.FilterRecommended and obj.system.recommended) or \
                   (self._filter == RevisionResultsProxyModel.FilterLatest and obj in obj.container.latest_revisions.values())


class RevisionResultsView(QTreeView):
    def __init__(self, parent, **kwargs):
        self._filter = RevisionResultsProxyModel.FilterAll
        super(RevisionResultsView, self).__init__(parent, **kwargs)
        self._worker = None

        # create and set a new model
        model = RevisionResultsModel(self)
        proxy_model = RevisionResultsProxyModel(self)
        proxy_model.setSourceModel(model)
        proxy_model.rowsInserted.connect(self._resizeColumns)
        self.setModel(proxy_model)

    def filter(self):
        return self._filter
    def setFilter(self, filter):
        self._filter = filter
        if self.model():
            self.model().setFilter(filter)

    def _cleanUpWorker(self, worker):
        del worker

    @pyqtSlot(list)
    def setConstraints(self, constraints):
        if self._worker is not None:
            # clean it up five seconds in the future
            QTimer.singleShot(5000, lambda worker=self._worker: self._cleanUpWorker(worker))
        
        if len(constraints) > 0:
            QApplication.setOverrideCursor(Qt.BusyCursor)
            self._worker = RevisionQueryWorker(constraints)
            self._worker.output.connect(self._setResultSets)
            self._worker.start()
        else:
            self._worker = None
            self.model().sourceModel().setResultSets([])

    def _setResultSets(self, result_sets):
        self.model().sourceModel().setResultSets(result_sets)
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

class RevisionQueryWorker(QThread):
    def __init__(self, constraints):
        super(RevisionQueryWorker, self).__init__()
        self._objs = constraints
        self.stopped = False

    output = pyqtSignal(list)
    
    def __del__(self):
        self.stopped = True
        while self.isRunning():
            self.wait()
    
    def run(self):
        assert self._objs > 0
        constraints = []
        # add label constraints
        constraints += ["container has_label %s" % l for l in self._objs if isinstance(l, tank.TankLabel)]
        # add container type constraints
        constraints += ["container is_type %s" % ct for ct in self._objs if isinstance(ct, tank.TankType) and \
                                                                      ct.properties.container_type == tank.constants.ContainerType.CONTAINER]
        # get revision types
        revision_types = [rt for rt in self._objs if isinstance(rt, tank.TankType) and rt.properties.container_type == tank.constants.ContainerType.REVISION]
        
        # default to all revision types if none are specified
        if len(revision_types) == 0:
            revision_types = tank.list_revision_types()
            # FIXME: ContainerGlobals search currently returns system containers as well (#12103)
            #revision_types = ["RevisionGlobals"]
        
        # find all revisions that match
        result_sets = []
        if len(constraints) > 0: 
            for rt in revision_types:
                if self.stopped:
                    return
                result_sets.append(tank.get_children(rt, constraints))
    
        # send the output signal with the results
        if not self.stopped:
            self.output.emit(result_sets)
