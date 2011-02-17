from PyQt4 import QtCore, QtGui

import tank

class Version(object):
    Version = 1
    CreatedBy = 2
    CreatedAt = 4
    Description = 8
    Status = 16

    def __init__(self, revision, display, bold=False, show_none=True):
        self._revision = revision
        self._display = display
        self._show_none = show_none
        self._bold = bold

    def textDocument(self, option=None):
        doc = QtGui.QTextDocument()
        doc.setUndoRedoEnabled(False)

        if option is not None:
            if option.state & QtGui.QStyle.State_Selected:
                text_color = "body {color:%s;}" % option.palette.highlightedText().color().name()
            else:
                text_color = "body {color:%s;}" % option.palette.text().color().name()
        else:
            text_color = ""

        doc.setDefaultStyleSheet(text_color + """
                                 body, html { margin:0; padding:0; }
                                 #version { text-align:left; }
                                 #created_by { text-align:left; font-size: 8pt; }
                                 #created_at { text-align:left; font-size: 8pt; }
                                 #description { text-align:left; font-size: 8pt; font-style: italic;}
                                 """)


        html = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'
        html += '<html lang="en"><header/><body>'

        version = self._revision.system.name
#        recommended = self._revision.system.recommended
        created_by = self._revision.properties.created_by.system.name if self._revision.properties.created_by is not None else None
        created_at = tank.common.propertytypes.DateTimePropertyType.utc_to_local_str(self._revision.system.creation_date)
        description = self._revision.properties.description

        if self._bold:
            html += "<b>"

        if self._display & self.Version and version is not None:
            html += '<div id="version">%s</div>' % version
#        if self._display & self.Status and status is not None:
#            try:
#                icon = {"outdated": ":images/red_x.png",
#                        "latest": ":images/yellow_exclamation.png",
#                        "recommended": ":images/green_check.png"}[status]
#                html += '<img src="%s">' % icon
#            except:
#                pass
        if self._display & self.CreatedBy and created_by is not None:
            html += '<div id="created_by">%s</div>' % created_by
        if self._display & self.CreatedAt and created_at is not None:
            html += '<div id="created_at">%s</div>' % created_at
        if self._display & self.Description and description is not None:
            html += '<div id="description">%s</div>' % description

        if self._bold:
            html += "</b>"

        html += "</body></html>"
        doc.setHtml(html)
        return doc

    def sizeHint(self, option):
        doc = self.textDocument()
        doc.setTextWidth(option.rect.width())
        return doc.size().toSize()

    def paint(self, painter, option):
        doc = self.textDocument(option)
        doc.setTextWidth(option.rect.width())
        painter.save()
        try:
            painter.translate(option.rect.topLeft())
            doc.drawContents(painter, QtCore.QRectF(0, 0, option.rect.width(), option.rect.height()))
        finally:
            painter.restore()


class VersionDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent, display):
        super(VersionDelegate, self).__init__(parent)
        self._display = display

    def sizeHint(self, option, index):
        revision = index.data(QtCore.Qt.UserRole).toPyObject()
        version = Version(revision, self._display)
        return version.sizeHint(option)

    def paint(self, painter, option, index):
        revision = index.data(QtCore.Qt.UserRole).toPyObject()

        bold = index.row() == self.parent().currentIndex()


        version = Version(revision, self._display, bold)

        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        version.paint(painter, option)


class VersionComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        self._revision = None
        super(VersionComboBox, self).__init__(parent)
        self.view().setResizeMode(QtGui.QListView.Adjust)
        self.view().setAlternatingRowColors(True)
        self.setItemDelegate(VersionDelegate(self, Version.Version|Version.CreatedBy|Version.CreatedAt|Version.Description))

    def sizeHint(self): #IGNORE:R0201
        return QtCore.QSize(200, 25)

    def revision(self):
        return self.itemData(self.currentIndex()).toPyObject()
    def setRevision(self, revision):
        self._revision = revision

        # update combo box items
        revisions = self._revision.container.revisions_dict[self._revision.system.type.system.name]
        versions = sorted(revisions.keys(), reverse=True)

        self.clear()
        for index, version in enumerate(versions):
            self.addItem(version, revisions[version])
            if str(self._revision) == str(revisions[version]):
                self.setCurrentIndex(index)

    def version(self):
        return self.currentText()


class RevisionTypeComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(RevisionTypeComboBox, self).__init__(parent)
        self.view().setAlternatingRowColors(True)
        self._validRevisionTypes = []

    def validRevisionTypes(self):
        return self._validRevisionTypes
    def setValidRevisionTypes(self, valid_rts):
        self._validRevisionTypes = valid_rts
        self.clear()
        for rt in valid_rts:
            self.addItem(rt.system.name if rt is not None else "<none>", rt)

    def currentRevisionType(self):
        return self.itemData(self.currentIndex()).toPyObject()
    def setCurrentRevisionType(self, rt):
        if rt is None:
            self.setCurrentIndex(0)
        else:
            try:
                self.setCurrentIndex(self._validRevisionTypes.index(rt))
            except ValueError:
                # trying to set a non-valid revision type, just set to none
                self.setCurrentIndex(0)


if __name__ == "__main__":
#    import tank
    app = QtGui.QApplication([])
    w = VersionComboBox()
    w.setRevision(tank.find("MayaScene(004, Anim_v2(anim, Sequence(01), Shot(01_0100)))"))
    w.show()
    app.exec_()
    print w.revision()
