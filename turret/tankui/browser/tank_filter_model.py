from PyQt4 import QtCore

import tank

class BaseItem(object):
    """Base class of Items"""
    def __init__(self, parent=None):
        self._parent = parent
        self._children = None

    @property
    def address(self):
        return None

    @property
    def parent(self):
        """Returns the parent object in the tree."""
        return self._parent

    @property
    def row(self):
        return self.parent.children.index(self)

    def __eq__(self, other):
        return other.name == self.name

    def __ne__(self, other):
        return other.name != self.name

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class RootItem(BaseItem):
    """The root of the Tank entity tree"""
    def __init__(self):
        super(RootItem, self).__init__()
        self.children = None

    def fetchMore(self):
        if self.children is None:
            self.children = [ContainerMetaItem(self), RevisionMetaItem(self)]
            self.children.extend(sorted([LabelTypeItem(tank.find(lt), self) for lt in tank.list_label_types()]))

class ContainerMetaItem(BaseItem):
    """Special class to be a parent to container types."""
    def __init__(self, parent):
        super(ContainerMetaItem, self).__init__(parent)
        self.children = None
        self.name = "Containers"

    def fetchMore(self):
        if self.children is None:
            self.children = sorted([ContainerTypeItem(tank.find(ct), self) for ct in tank.list_container_types()])


class ContainerTypeItem(BaseItem):
    """Special class to encapsulate container types."""
    def __init__(self, container_type, parent):
        super(ContainerTypeItem, self).__init__(parent)
        assert isinstance(container_type, tank.TankType) and container_type.properties.container_type == tank.constants.ContainerType.CONTAINER
        self.obj = self.container_type = container_type
        self.name = self.container_type.system.name
        self.children = []


class RevisionMetaItem(BaseItem):
    """Special class to be a parent to revision types."""
    def __init__(self, parent):
        super(RevisionMetaItem, self).__init__(parent)
        self.children = None
        self.name = "Revisions"

    def fetchMore(self):
        if self.children is None:
            self.children = sorted([RevisionTypeItem(tank.find(rt), self) for rt in tank.list_revision_types()])


class RevisionTypeItem(BaseItem):
    """Special class to encapsulate revision types."""
    def __init__(self, revision_type, parent):
        super(RevisionTypeItem, self).__init__(parent)
        assert isinstance(revision_type, tank.TankType) and revision_type.properties.container_type == tank.constants.ContainerType.REVISION
        self.obj = self.revision_type = revision_type
        self.name = revision_type.system.name
        self.children = []


class LabelTypeItem(BaseItem):
    """Encapsulates a Tank label type."""
    def __init__(self, label_type, parent):
        super(LabelTypeItem, self).__init__(parent)
        assert isinstance(label_type, tank.TankType) and label_type.properties.container_type == tank.constants.ContainerType.LABEL
        self.label_type = label_type
        self.children = None

    def fetchMore(self):
        if self.children is None:
            matching_labels = tank.get_children(self.label_type).fetch_all()
            self.children = sorted([LabelItem(label, self) for label in matching_labels])


    @property
    def name(self):
        return self.label_type.system.name


class LabelItem(BaseItem):
    """Encapsulates a Tank label."""
    def __init__(self, label, parent):
        super(LabelItem, self).__init__(parent)
        assert isinstance(label, tank.TankLabel) and label.system.name is not None
        self.obj = self.label = label
        self.children = []

    @property
    def name(self):
        return self.label.system.name


class Roles(object):
    MatchRole = QtCore.Qt.UserRole


class TankFilterModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(TankFilterModel, self).__init__(parent)
        self.root = RootItem()

    def hasChildren(self, parent):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()
        return not isinstance(parent_item, LabelItem)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()
        if parent_item.children is not None:
            return len(parent_item.children)
        else:
            return 0

    def canFetchMore(self, parent):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()
        return parent_item.children is None

    def fetchMore(self, parent):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()
        if parent_item.children is None:
            parent_item.fetchMore()
            self.beginInsertRows(parent, 0, len(parent_item.children))
            self.endInsertRows()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            if role == QtCore.Qt.DisplayRole:
                result = "Right click to add a label"
            else:
                result = None
        else:
            if role == QtCore.Qt.DisplayRole:
                item = index.internalPointer()
                result = item.name
            elif role == Roles.MatchRole:
                if index.column() == 0:
                    item = index.internalPointer()
                    result = item.name
                else:
                    result = None
            else:
                result = None
        return QtCore.QVariant(result)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            item = self.root.children[row]
            return self.createIndex(row, column, item)
        else:
            parent_item = parent.internalPointer()
            child_item = parent_item.children[row]
            return self.createIndex(row, column, child_item)

    def match(self, start, role, value, hits=1, flags=QtCore.Qt.MatchStartsWith|QtCore.Qt.MatchWrap):
        # for whatever reason, this does not appear to be implemented
        result = []
        for row in range(0, self.rowCount(start)):
            for column in range(0, self.columnCount(start)):
                if self.hasIndex(row, column, start):
                    index = self.index(row, column, start)
                    data = self.data(index, role)
                    if data == value:
                        result.append(index)
        return result

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        index_item = index.internalPointer()
        parent_item = index_item.parent

        if isinstance(parent_item, RootItem):
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row, 0, parent_item)

