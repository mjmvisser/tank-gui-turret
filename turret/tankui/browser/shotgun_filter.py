from PyQt4 import QtCore, QtGui

import tank
from .filter_view import FilterView

# BIG WTF... how do I get these without digging into "private" APIs?
sg_project_id = int(tank.common._constants.get_typed_connectivity_settings()["shotgun_project_id"])
sg = tank.util.misc.get_shotgun_connection()

class BaseItem(object):
    """Base class of Items"""
    def __init__(self, parent=None):
        self.parent = parent
        self.children = []
        self.address = None

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
    """The root of the Shotgun entity tree"""
    def __init__(self, include_revision_types=False):
        super(RootItem, self).__init__()
        self.obj = None
        self.children = [ContainerMetaItem(self)]
        if include_revision_types:
            self.children.append(RevisionMetaItem(self))
        self.children.extend(sorted([EntityTypeItem(entity, link_fields, self) \
                                     for entity, link_fields in (("Sequence", []),
                                                                 ("Shot", ["sg_sequence", "assets"]),
                                                                 ("Asset", []))]))

class ContainerMetaItem(BaseItem):
    """Special class to be a parent to container types."""
    def __init__(self, parent):
        super(ContainerMetaItem, self).__init__(parent)
        self.children = None
        self.name = "Containers"
        self.obj = None

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
        self.obj = None

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


class EntityTypeItem(BaseItem):
    """Encapsulates a Shotgun entity type."""
    def __init__(self, entity_type, link_fields, parent):
        super(EntityTypeItem, self).__init__(parent)
        self.entity_type = entity_type
        self.link_fields = link_fields
        self.children = None
        self.name = entity_type
        self.obj = None

    def fetchMore(self):
        if self.children is None:
            matching_entities = sg.find(self.entity_type, filters=[["project", "is", {"type": "Project", "id": sg_project_id}]], fields=["code", "id"] + self.link_fields)
            self.children = sorted([EntityItem(entity, self) for entity in matching_entities])


class EntityItem(BaseItem):
    """Encapsulates a Shotgun entity."""
    def __init__(self, entity, parent):
        super(EntityItem, self).__init__(parent)
        self.entity = {"type": entity["type"], "id": entity["id"]}
        self.children = []
        self.name = entity["code"]
        self._obj = None

        # unpack entity link fields into a single list
        self.links = []
        for v in self.entity.values():
            if isinstance(v, dict):
                # it's a dictionary
                self.links.append({"type": v["type"], "id": v["id"]})
            elif isinstance(v, (tuple, list)):
                # it's a list
                for i in v:
                    self.links.append({"type": i["type"], "id": i["id"]})

    @property
    def obj(self):
        if not self._obj:
            # look up the corresponding label in tank
            for lt in tank.list_label_types():
                results = tank.get_children(lt, filters=["shotgun_entity is %s,%d" % (self.entity["type"], self.entity["id"])]).fetch_all()
                if len(results) != 0:
                    self._obj = results[0]
        return self._obj

class ShotgunFilterModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(ShotgunFilterModel, self).__init__(parent)
        self.root = RootItem()
        self._includeRevisionTypes = False

    def includeRevisionTypes(self):
        return self._includeRevisionTypes
    def setIncludeRevisionTypes(self, flag):
        self.beginResetModel()
        self.root = RootItem(include_revision_types=flag)
        self._includeRevisionTypes = flag
        self.endResetModel()

    def hasChildren(self, parent):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()
        return parent_item.children != []

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
                result = "Right click to add an entity"
            else:
                result = None
        else:
            if role == QtCore.Qt.DisplayRole:
                item = index.internalPointer()
                result = item.name
            elif role == QtCore.Qt.UserRole:
                item = index.internalPointer()
                result = item
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

class LabelCullProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None, **kwargs):
        self._includeRevisionTypes = False
        self._validContainerTypes = [tank.find(ct) for ct in tank.list_container_types()]
        self._selectionModel = None
        super(LabelCullProxyModel, self).__init__(parent, dynamicSortFilter=True, **kwargs)

    def columnAcceptsRow(self, sourceColumn, sourceParent):
        return True

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._selectionModel:
            return True

        parent = self.mapFromSource(source_parent)
        #parent_item = source_parent.data(QtCore.Qt.UserRole).toPyObject()
        source_index = source_parent.child(source_row, 0)
        index = self.mapFromSource(source_index)
        item = source_index.data(QtCore.Qt.UserRole).toPyObject()

        # invalid parent means top-level items
        if not source_parent.isValid():
            if isinstance(item, RevisionMetaItem):
                # cull revision types if not enabled
                return self._includeRevisionTypes
            else:
                return True

        if not self._selectionModel.isSelected(parent):
            # parent not selected, thus not visible so pass through
            return True

        if self._selectionModel.isSelected(index):
            # don't cull if the item is selected
            return True

#        if isinstance(parent_item, ContainerMetaItem):
#            # cull invalid container types
#            return item.obj in self._validContainerTypes

        if isinstance(item, EntityItem):
            # get a list of selected labels
            items = [i.data(QtCore.Qt.UserRole).toPyObject() for i in self._selectionModel.selectedIndexes()]
            selected_items = [i for i in items if isinstance(i, EntityItem)]

            selected_entities = [item.entity for item in selected_items]

            # show the item only if all of its links are selected
            return all((link in selected_entities) for link in item.links)
        else:
            # don't cull non-entities
            return True

    def match(self, start, role, value, hits=1, flags=QtCore.Qt.MatchStartsWith|QtCore.Qt.MatchWrap):
        # not correctly implemented in Qt 4.6
        source_start = self.mapToSource(start)
        return [self.mapFromSource(index) for index in self.sourceModel().match(source_start, role, value, hits, flags)]

    def includeRevisionTypes(self):
        return self._includeRevisionTypes
    def setIncludeRevisionTypes(self, flag):
        self._includeRevisionTypes = flag

    def validContainerTypes(self):
        return self._validContainerTypes
    def setValidContainerTypes(self, valid_container_types):
        self._validContainerTypes = valid_container_types

    def selectionModel(self):
        return self._selectionModel
    def setSelectionModel(self, selection_model):
        self._selectionModel = selection_model
        self._selectionModel.selectionChanged.connect(self.invalidateFilter)

    def _updateSelection(self, selected, deselected):
        objects = []
        for index in self.mapSelectionToSource(self.selectionModel.selection()).indexes():
            parent = index.parent()
            if parent.isValid():
                parent_item = parent.data(QtCore.Qt.UserRole)
                if isinstance(parent_item, EntityTypeItem):
                    obj = index.data(QtCore.Qt.EditRole)
                    objects.append(obj)


        #matching_entities = sg.find(self.entity_type, filters=[["project", "is", {"type": "Project", "id": sg_project_id}]], fields=["code", "id"])


class ShotgunFilterView(FilterView):
    def __init__(self, parent=None):
        super(ShotgunFilterView, self).__init__(parent)

        model = ShotgunFilterModel(self)
        #proxy_model = LabelCullProxyModel(self)
        #proxy_model.setSourceModel(model)

        self.setModel(model)

        # no selection model until a model has been set
        # for proxy model
        #self.model().setSelectionModel(self.selectionModel())

    def select(self, obj):
        self.selectionModel().clear()
        # for proxy model
        #self.model().setSelectionModel(self.selectionModel())
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
