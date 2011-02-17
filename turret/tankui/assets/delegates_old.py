from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .model import Columns
from ..container import ContainerEdit
from ..revision import Version, VersionComboBox, RevisionTypeComboBox

class AssetsItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(AssetsItemDelegate, self).__init__(parent)

#    def _dataFromNode(self, node):
#        return {"version": node.version, 
#                "status": node.status,
#                "created_by": node.created_by,
#                "created_at": node.created_at,
#                "description": node.description}

#    def createEditor(self, parent, option, index):
#        # the index we are passed is from the proxy; we first
#        # need to call mapToSource to return the original index
#        node = index.model().data(index, Qt.UserRole).toPyObject()
#        if index.column() == Columns.Container:
#            editor = BrowserDialog(BrowserDialog.BrowseContainers, parent=parent, modal=True)
#            return editor
#        elif index.column() == Columns.RevisionType:
#            editor = RevisionTypeComboBox(parent)
#            editor.setValidRevisionTypes(node.valid_revision_types())
#            return editor
#        elif index.column() == Columns.Version:
#            editor = VersionComboBox(parent)
#            editor.setValidVersions(node.valid_versions())
#            return editor
#        else:
#            return super(AssetsItemDelegate, self).createEditor(parent, option, index)
#
#    def setEditorData(self, editor, index):
#        if index.column() == Columns.Container:
#            value = index.model().data(index, Qt.EditRole).toPyObject()
#            editor.setCurrentContainer(value)
#            # try to set some sane defaults
#            if value is None:
#                # FIXME: is there be a better way to get the labels rather than directly from the scene?
#                editor.setCurrentLabels(index.model().sourceModel().root().labels.values())
#        elif index.column() == Columns.RevisionType:
#            value = index.model().data(index, Qt.EditRole).toPyObject()
#            editor.setCurrentRevisionType(value)
#        elif index.column() == Columns.Version:
#            value = index.model().data(index, Qt.EditRole).toPyObject()
#            editor.setCurrentVersion(str(value))
#        else:
#            super(AssetsItemDelegate, self).setEditorData(editor, index)
#
#    def setModelData(self, editor, model, index):
#        if index.column() == Columns.Container:
#            model.setData(index, editor.currentContainer(), Qt.EditRole)
#        elif index.column() == Columns.RevisionType:
#            model.setData(index, editor.currentRevisionType(), Qt.EditRole)
#        elif index.column() == Columns.Version:
#            model.setData(index, editor.currentVersion(), Qt.EditRole)
#        else:
#            super(AssetsItemDelegate, self).setModelData(editor, model, index)
#
#    def updateEditorGeometry(self, editor, option, index):
#        editor.setGeometry(option.rect)
#
    def sizeHint(self, option, index):
        if index.column() == Columns.Version:
            data = index.data(Qt.UserRole).toMap()
            version = Version(data, Version.Version|Version.Status)
            return version.sizeHint(option)
        else:
            return super(AssetsItemDelegate, self).sizeHint(option, index)

#    def initStyleOption(self, option, index):
#        super(AssetsItemDelegate, self).initStyleOption(option, index)
#        if index.column() == Columns.PATH:
#            # override the elideMode to put the ellipsis on the left for the PATH so
#            # the filename is visible
#            option.textElideMode = Qt.ElideLeft
            
    def paint(self, painter, option, index):
        if index.column() == Columns.Version:
            opt = QStyleOptionViewItemV4(option)
            self.initStyleOption(opt, index)
            
            node = index.data(Qt.UserRole).toPyObject()
            
            data = {"version": node.version, 
                    "status": node.status,
                    "created_by": node.created_by,
                    "created_at": node.created_at,
                    "description": node.description}
            version = Version(data, Version.Version|Version.Status, False)

            bg_brush = index.data(Qt.BackgroundRole).toPyObject()

            # fill background
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, opt.palette.highlight())
            else:
                painter.fillRect(option.rect, bg_brush)

            version.paint(painter, option)
        else:
            super(AssetsItemDelegate, self).paint(painter, option, index)


