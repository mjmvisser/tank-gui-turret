from PyQt4 import QtCore, QtGui

import tank

from .filter_view import FilterView
from ..utils import pyqtOverrideCursor

#import pydevd; pydevd.settrace(suspend=False)

class BaseItem(object):
    """Base class of Items"""
    def __init__(self, parent=None):
        self.parent = parent
        self.obj = None
        self.address = None
        self.children = []

    @property
    def row(self):
        return self.parent.children.index(self)

    def __eq__(self, other):
        # generic equivalence test from http://stackoverflow.com/questions/390250/elegant-ways-to-support-equivalence-equality-in-python-classes
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class RootItem(BaseItem):
    """The root of the Tank entity tree"""
    def __init__(self):
        super(RootItem, self).__init__()
        self.children = [RevisionMetaItem(self), ContainerMetaItem(self)]
        self.children.extend(sorted([LabelTypeItem(tank.find(lt), self) for lt in tank.list_label_types()]))

class ContainerMetaItem(BaseItem):
    """Special class to be a parent to container types."""
    def __init__(self, parent):
        super(ContainerMetaItem, self).__init__(parent)
        self.children = None
        self.name = "Containers"

    def fetchMore(self):
        if self.children is None:
            return sorted([ContainerTypeItem(tank.find(ct), self) for ct in tank.list_container_types()])


class ContainerTypeItem(BaseItem):
    """Special class to encapsulate container types."""
    def __init__(self, container_type, parent):
        super(ContainerTypeItem, self).__init__(parent)
        assert isinstance(container_type, tank.TankType) and container_type.properties.container_type == tank.constants.ContainerType.CONTAINER
        self.obj = self.container_type = container_type
        self.name = self.container_type.system.name


class RevisionMetaItem(BaseItem):
    """Special class to be a parent to revision types."""
    def __init__(self, parent):
        super(RevisionMetaItem, self).__init__(parent)
        self.children = None
        self.name = "Revisions"

    def fetchMore(self):
        if self.children is None:
            return sorted([RevisionTypeItem(tank.find(rt), self) for rt in tank.list_revision_types()])


class RevisionTypeItem(BaseItem):
    """Special class to encapsulate revision types."""
    def __init__(self, revision_type, parent):
        super(RevisionTypeItem, self).__init__(parent)
        assert isinstance(revision_type, tank.TankType) and revision_type.properties.container_type == tank.constants.ContainerType.REVISION
        self.obj = self.revision_type = revision_type
        self.name = revision_type.system.name


class LabelTypeItem(BaseItem):
    """Encapsulates a Tank label type."""
    def __init__(self, label_type, parent):
        super(LabelTypeItem, self).__init__(parent)
        assert isinstance(label_type, tank.TankType) and label_type.properties.container_type == tank.constants.ContainerType.LABEL
        self.obj = self.label_type = label_type
        self.children = None

    def fetchMore(self):
        if self.children is None:
            matching_labels = tank.get_children(self.label_type).fetch_all()
            return sorted([LabelItem(label, self) for label in matching_labels])

    @property
    def name(self):
        return self.label_type.system.name


class LabelItem(BaseItem):
    """Encapsulates a Tank label."""
    def __init__(self, label, parent):
        super(LabelItem, self).__init__(parent)
        assert isinstance(label, tank.TankLabel) and label.system.name is not None
        self.obj = self.label = label

    @property
    def name(self):
        return self.label.system.name



class TankFilterModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(TankFilterModel, self).__init__(parent)
        self._root = RootItem()

    def hasChildren(self, parent):
        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()
        return parent_item.children != []

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()
        if parent_item.children is not None:
            return len(parent_item.children)
        else:
            return 0

    def canFetchMore(self, parent):
        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()
        return parent_item.children is None

    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def fetchMore(self, parent):
        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()
        if parent_item.children is None:
            children = parent_item.fetchMore()
            self.beginInsertRows(parent, 0, len(children)-1)
            parent_item.children = children
            self.endInsertRows()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        result = None
        if not index.isValid():
            if role == QtCore.Qt.DisplayRole:
                result = "Right click to add a label"
        else:
            if role == QtCore.Qt.DisplayRole:
                item = index.internalPointer()
                result = item.name
            elif role == QtCore.Qt.UserRole:
                result = index.internalPointer()

        return QtCore.QVariant(result)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            item = self._root.children[row]
            return self.createIndex(row, column, item)
        else:
            parent_item = parent.internalPointer()
            child_item = parent_item.children[row]
            return self.createIndex(row, column, child_item)

    def match(self, start, role, value, hits=1, flags=QtCore.Qt.MatchStartsWith|QtCore.Qt.MatchWrap):
        assert role == QtCore.Qt.UserRole
        # reimplement to do a recursive search
        # only support QtCore.Qt.UserRole for now
        # only support 1 hit
        result = []
        try:
            item = start.data(role).toPyObject().obj
        except AttributeError:
            item = None

        if item == value:
            return [start]

        if self.hasChildren(start):
            if self.canFetchMore(start):
                self.fetchMore(start)
            for row in range(0, self.rowCount(start)):
                index = self.index(row, 0, start)
                result = self.match(index, role, value, hits, flags)
                if len(result) > 0:
                    return result

        return result

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        index_item = index.internalPointer()
        parent_item = index_item.parent

        if isinstance(parent_item, RootItem):
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row, 0, parent_item)


class LabelCullProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None, **kwargs):
        super(LabelCullProxyModel, self).__init__(parent, dynamicSortFilter=True, **kwargs)
        self._includeRevisionTypes = False
        self._validContainerTypes = frozenset(tank.find(ct) for ct in tank.list_container_types())
        self._validRevisionTypes = frozenset(tank.find(rt) for rt in tank.list_revision_types())
        self._selectionModel = None

    def columnAcceptsRow(self, source_column, source_parent):
        return True

    def filterAcceptsRow(self, source_row, source_parent):
        parent = self.mapFromSource(source_parent)
        source_parent_item = source_parent.data(QtCore.Qt.UserRole).toPyObject()
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        source_item = source_index.data(QtCore.Qt.UserRole).toPyObject()

        if source_parent_item is None and isinstance(source_item, RevisionMetaItem) and not self._includeRevisionTypes:
            # cull revision types if not enabled
            return False

        if not self._selectionModel:
            return True

        # invalid parent means top-level items
        if not source_parent.isValid():
            return True

        if isinstance(source_parent_item, ContainerMetaItem):
            # cull invalid container types
            return source_item.obj in self._validContainerTypes

        if isinstance(source_parent_item, RevisionMetaItem):
            # cull invalid revision types
            return source_item.obj in self._validRevisionTypes

        if any(self._selectionModel.isRowSelected(row, parent) for row in range(0, self.rowCount(parent))):
            # don't cull if any item is selected
            return True

        if isinstance(source_item, LabelItem):
            label_type = source_item.parent.obj
            if self._matchingLabels.has_key(label_type):
                return source_item.obj in self._matchingLabels[label_type]

        return True


    def match(self, start, role, value, hits=1, flags=QtCore.Qt.MatchStartsWith|QtCore.Qt.MatchWrap):
        # not correctly implemented in Qt 4.6
        source_start = self.mapToSource(start)
        return [self.mapFromSource(index) for index in self.sourceModel().match(source_start, role, value, hits, flags)]

    def includeRevisionTypes(self):
        return self._includeRevisionTypes
    def setIncludeRevisionTypes(self, flag):
        self._includeRevisionTypes = flag
        self.invalidateFilter()

    def validContainerTypes(self):
        return self._validContainerTypes
    def setValidContainerTypes(self, valid_container_types):
        self._validContainerTypes = frozenset(valid_container_types)
        self.invalidateFilter()

    def validRevisionTypes(self):
        return self._validRevisionTypes
    def setValidRevisionTypes(self, valid_revision_types):
        self._validRevisionTypes = frozenset(valid_revision_types)
        self.invalidateFilter()

    def selectionModel(self):
        return self._selectionModel
    def setSelectionModel(self, selection_model):
        self._selectionModel = selection_model
        self._matchingLabels = {}
        self._selectionChanged()
        self._selectionModel.selectionChanged.connect(self._selectionChanged)

    @QtCore.pyqtSlot()
    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def _selectionChanged(self):
        # cache valid labels per-top-level item
        selected_items = [i.data(QtCore.Qt.UserRole).toPyObject() for i in self._selectionModel.selectedIndexes()]
        selected_labels = [i.obj for i in selected_items if isinstance(i, LabelItem)]
        selected_label_types = [i.obj for i in selected_items if isinstance(i, LabelTypeItem)]

        self._matchingLabels = dict((label_type, set(tank.label_cross_search(label_type, selected_labels).fetch_all())) for label_type in selected_label_types)

        self.invalidateFilter()


class TankFilterView(FilterView):
    def __init__(self, parent=None):
        super(TankFilterView, self).__init__(parent)

        model = TankFilterModel(self)
        proxy_model = LabelCullProxyModel(self)
        proxy_model.setSourceModel(model)

        self.setModel(proxy_model)

        # no selection model until a model has been set
        self.model().setSelectionModel(self.selectionModel())

        self.selectionModel().selectionChanged.connect(self._updateAutoSelect)

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def _updateAutoSelect(self, selected, deselected):
        # if a ContainerTypeItem has been selected, grab its label types and
        # select those as well
        sel = QtGui.QItemSelection()
        for index in selected.indexes():
            item = index.data(QtCore.Qt.UserRole).toPyObject()
            if isinstance(item, ContainerTypeItem):
                for label_type in (d["type"] for d in item.obj.label_types.values() if not d["is_optional"]):
                    label_index = self.model().match(QtCore.QModelIndex(), QtCore.Qt.UserRole, label_type)[0]
                    if not self.selectionModel().isSelected(label_index):
                        sel.select(label_index, label_index)
                break

        self.selectionModel().select(sel, QtGui.QItemSelectionModel.Select)

    def visibleFilters(self):
        # top-level items are the column names
        return [index.data() for index in self.selectionModel().selectedIndexes() if not index.parent().isValid()]
    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def setVisibleFilters(self, filters):
        selection = QtGui.QItemSelection()
        for item in filters:
            for index in self.model().match(QtCore.QModelIndex(), QtCore.Qt.UserRole, item, 1, QtCore.Qt.MatchFlags(QtCore.Qt.MatchFixedString)):
                selection.select(index, index)
        self.selectionModel().select(selection, QtGui.QItemSelectionModel.Select)

    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def select(self, obj):
        self.selectionModel().clear()
        self.model().setSelectionModel(self.selectionModel())
        if obj is not None:
            # build an item selection
            selection = QtGui.QItemSelection()
            if isinstance(obj, tank.TankContainer):
                search = obj.labels.values() + [obj.system.type]
            elif isinstance(obj, tank.TankRevision):
                search = obj.container.labels.values() + [obj.container.system.type] + [obj.system.type]
            else:
                search = []

            for matches in [self.model().match(QtCore.QModelIndex(), QtCore.Qt.UserRole, obj, 1, QtCore.Qt.MatchExactly) for obj in search]:
                for match in matches:
                    parent = match.parent()
                    selection.select(parent, parent)
                    selection.select(match, match)

            # select it
            self.selectionModel().select(selection, QtGui.QItemSelectionModel.Select)

    def selectedObjects(self):
        return [index.data(QtCore.Qt.UserRole).toPyObject().obj for index in self.selectionModel().selectedIndexes()]
