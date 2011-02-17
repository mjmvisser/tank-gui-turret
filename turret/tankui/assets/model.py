from PyQt4 import QtCore, QtGui

from ..utils import pyqtOverrideCursor #IGNORE:F0401

from ...tankscene import Scene #IGNORE:F0401

from . import icons_rc #@UnusedImport #IGNORE:W0611


class Filters(object): #IGNORE:R0903
    Working = 1
    Revision = 2
    Other = 4
    All = Working|Revision|Other

class Columns(object): #IGNORE:R0903
    Node,          \
    ContainerName, \
    Container,     \
    Revision,      \
    RevisionType,  \
    Version,       \
    Path,          \
    CreatedBy,     \
    CreatedAt,     \
    Description,   \
    NumColumns = range(0, 11)

    @staticmethod
    def name(value):
        return ("Node",
                "Name",
                "Container",
                "Revision",
                "Type",
                "Version",
                "Path",
                "Created By",
                "Created At",
                "Description")[value]

def _createBadgedImage(image, badge):
    badged_image = QtGui.QImage(image.size(), QtGui.QImage.Format_ARGB32_Premultiplied)

    painter = QtGui.QPainter(badged_image)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
    painter.fillRect(badged_image.rect(), QtCore.Qt.transparent)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, image)

    # half-height badge in the bottom left
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    painter.scale(0.5, 0.5)
    painter.drawImage(0, image.height(), badge)

    return badged_image


class AssetsModel(QtCore.QAbstractItemModel):
    def __init__(self, parent, **kwargs):
        self._root = None
        self._editingEnabled = False
        super(AssetsModel, self).__init__(parent, **kwargs)

    def editingEnabled(self):
        return self._editingEnabled
    def setEditingEnabled(self, flag):
        self.beginResetModel()
        self._editingEnabled = flag
        self.endResetModel()

    def root(self):
        return self._root
    def setRoot(self, root):
        self.beginResetModel()
        self._root = root
        self.endResetModel()

    def columnCount(self, parent=QtCore.QModelIndex()): #IGNORE:R0201
        return Columns.NumColumns

    def rowCount(self, parent=QtCore.QModelIndex()): #IGNORE:R0201
        if not parent.isValid():
            # invalid parent means root node, means the scene, of which there can only be one
            return 1
        else:
            parent_node = parent.internalPointer()
            return len(parent_node.dependencies)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return super(AssetsModel, self).headerData(section, orientation, role)
        else:
            return QtCore.QVariant(Columns.name(section))

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        node = index.internalPointer()

        flags = super(AssetsModel, self).flags(index)

        if self._editingEnabled:
            if index.column() == Columns.Node:
                flags |= QtCore.Qt.ItemIsEditable
            elif index.column() in (Columns.Container, Columns.RevisionType) and not node.is_revision():
                flags |= QtCore.Qt.ItemIsEditable
            elif index.column() == Columns.ContainerName and not node.is_revision() and node.container is not None and node.container.system.type.properties.use_name:
                flags |= QtCore.Qt.ItemIsEditable
            elif index.column() == Columns.Version and node.is_revision():
                flags |= QtCore.Qt.ItemIsEditable

        return flags

    def data(self, index, role=QtCore.Qt.DisplayRole): #IGNORE:R0201
        if not index.isValid():
            result = None
        else:
            node = index.internalPointer()

            result = None

            if role == QtCore.Qt.DisplayRole:
                # render each column's data
                if index.column() == Columns.Node:
                    result = node.node
                elif index.column() == Columns.ContainerName:
                    result = node.name
                elif index.column() == Columns.Container:
                    result = node.container_address
                elif index.column() == Columns.Revision:
                    if node.revision:
                        result = node.revision.system.address
                elif index.column() == Columns.RevisionType:
                    if node.revision_type:
                        result = node.revision_type.system.name
                elif index.column() == Columns.Version:
                    if node.is_revision():
                        result = node.version
                    elif node.is_working():
                        result = "Working"
                elif index.column() == Columns.Path:
                    result = node.path
                elif index.column() == Columns.CreatedBy:
                    result = node.created_by
                elif index.column() == Columns.CreatedAt:
                    result = node.created_at
                elif index.column() == Columns.Description:
                    result = node.description
            elif role == QtCore.Qt.EditRole:
                if index.column() == Columns.Node:
                    result = node.node
                elif index.column() == Columns.ContainerName:
                    result = node.name
                elif index.column() == Columns.Container:
                    result = node.container
                elif index.column() == Columns.Revision:
                    result = node.revision
                elif index.column() == Columns.RevisionType:
                    result = node.revision_type
                elif index.column() == Columns.Version:
                    # pass the revision instead of the version
                    # otherwise the combo box won't know what to show
                    # in its drop-down
                    result = node.revision
            elif role == QtCore.Qt.UserRole:
                result = node
            elif role == QtCore.Qt.FontRole:
                if node.is_removed():
                    font = QtGui.QFont()
                    font.setStrikeOut(True)
                    result = font
                elif node.is_dirty():
                    # italics
                    font = QtGui.QFont()
                    font.setItalic(True)
                    result = font
            elif role == QtCore.Qt.BackgroundRole:
                if node.is_dirty():
                    # pretty blue
                    brush = QtGui.QBrush(QtGui.QColor(153, 204, 255, 255))
                    result = brush
            elif role == QtCore.Qt.DecorationRole:
                if index.column() == Columns.Node:
                    if node.is_working():
                        result = QtGui.QImage(":images/hollow_disc.png")
                    elif node.is_revision():
                        status = node.status
                        if status.startswith("general+"):
                            if "latest" in status:
                                result = QtGui.QImage(":images/green_halfdisc.png")
                            elif "outofdate" in status:
                                result = QtGui.QImage(":images/red_halfdisc.png")
                            else:
                                result = QtGui.QImage(":images/question_disc.png")
                        elif status.startswith("recommended+"):
                            if "latest" in status:
                                result = QtGui.QImage(":images/green_disc.png")
                            elif "outofdate" in status:
                                result = QtGui.QImage(":images/red_disc.png")
                            else:
                                result = QtGui.QImage(":images/question_disc.png")
                    else:
                        result = QtGui.QImage(":images/question_disc.png")
            elif role == QtCore.Qt.SizeHintRole:
                if index.column() == Columns.Node:
                    return QtCore.QSize(24, 24)
            elif role == QtCore.Qt.ToolTipRole:
                if index.column() == Columns.Node:
                    if node.is_working():
                        result = "Working"
                    elif node.is_revision():
                        status = node.status
                        if "latest" in status:
                            result = "Up-to-date"
                        elif "outofdate" in status:
                            result = "Out-of-date"
                        else:
                            result = "Unknown"
                    else:
                        result = "Unknown"

        return QtCore.QVariant(result)

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        node = index.internalPointer()

        changed = False

        if role == QtCore.Qt.EditRole:
            if index.column() == Columns.Node:
                node.node = str(value.toString())
                changed = True
            elif index.column() == Columns.ContainerName:
                node.name = str(value.toString())
                changed = True
            elif index.column() == Columns.Container:
                node.container = value.toPyObject()
                changed = True
            elif index.column() == Columns.Revision:
                node.revision = value.toPyObject()
                changed = True
            elif index.column() == Columns.RevisionType:
                node.revision_type = value.toPyObject()
                changed = True
            elif index.column() == Columns.Version:
                node.version = str(value.toString())
                changed = True

        if changed:
            self.dataChanged.emit(index, index)

        return changed

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self._root or not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            return self.createIndex(row, column, self._root)
        else:
            parent_node = parent.internalPointer()
            child_node = parent_node.dependencies[row]
            return self.createIndex(row, column, child_node)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        index_node = index.internalPointer()
        parent_node = index_node.parent

        if parent_node is None:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(parent_node.row, 0, parent_node)

    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def refresh(self):
        self.layoutAboutToBeChanged.emit()

        self.beginResetModel()
        self._root = Scene(self._root.delegate)
        self.endResetModel()

    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def addDependency(self, path, delegate):
        self.layoutAboutToBeChanged.emit()

        self.beginResetModel()
        self._root.add_dependency(path, delegate=delegate)
        self.endResetModel()

    def remove(self, indexes):
        self.layoutAboutToBeChanged.emit()
        for index in indexes:
            if index.column() == Columns.Node:
                node = index.internalPointer()
                node.remove()
        self.layoutChanged.emit()


class SortFilterAssetsModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent, **kwargs):
        self._typeFilter = Filters.All
        self._searchString = None
        super(SortFilterAssetsModel, self).__init__(parent, dynamicSortFilter=True, **kwargs)

    def typeFilter(self):
        return self._typeFilter
    def setTypeFilter(self, type_filter):
        self._typeFilter = type_filter
        self.invalidateFilter()

    def searchString(self):
        return self._searchString
    def setSearchString(self, search_string):
        self._searchString = search_string
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        # always pass through the top-level node, otherwise filter is useless
        if not sourceParent.isValid():
            return True

        index = self.sourceModel().index(sourceRow, Columns.Path, sourceParent)
        node = index.data(QtCore.Qt.UserRole).toPyObject()

        if not node:
            return True

        passes_filter = (self._typeFilter == Filters.All) or \
                        (self._typeFilter & Filters.Working and node.is_working()) or \
                        (self._typeFilter & Filters.Revision and node.is_revision()) or \
                        (self._typeFilter & Filters.Other and not node.is_working() and not node.is_revision())

        matches_search = not self._searchString or node.matches(self._searchString)


        return passes_filter and matches_search
