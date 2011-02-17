import os
from PyQt4 import QtCore, QtGui

import tank

from ..browser import BrowserDialog #IGNORE:F0401
from ..revision import RevisionTypeComboBox #IGNORE:F0401
from ..utils import pyqtOverrideCursor #IGNORE:F0401
from ... import plugins

from . import icons_rc #IGNORE:W0611 #@UnusedImport

class ProductGroupWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ProductGroupWidget, self).__init__(parent)
        self._cwd = os.getcwd()
        self._path = None
        self._frameRange = None
        self._container = None

        mlayout = QtGui.QHBoxLayout(margin=0)
        vlayout = QtGui.QVBoxLayout(margin=0)

        groupbox = QtGui.QGroupBox("Product")
        groupbox_layout = QtGui.QVBoxLayout()
        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel("File:")
        hlayout.addWidget(label)
        self._product = QtGui.QLineEdit(enabled=False)
        browse_product_button = QtGui.QPushButton("Browse...")
        hlayout.addWidget(self._product)
        hlayout.addWidget(browse_product_button)
        groupbox_layout.addLayout(hlayout)

        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Container:")
        self._containerEdit = QtGui.QLineEdit(enabled=False)
        browse_source_button = QtGui.QPushButton("Browse...")
        hlayout.addWidget(label)
        hlayout.addWidget(self._containerEdit)
        hlayout.addWidget(browse_source_button)
        groupbox_layout.addLayout(hlayout)

        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Revision Type:")
        self._revisionType = RevisionTypeComboBox(self)

        hlayout.addWidget(label)
        hlayout.addWidget(self._revisionType)
        hlayout.addStretch(1)
        groupbox_layout.addLayout(hlayout)

        groupbox.setLayout(groupbox_layout)
        vlayout.addWidget(groupbox)

        mlayout.addLayout(vlayout)

        vlayout = QtGui.QVBoxLayout(margin=0)

        remove_button = QtGui.QPushButton()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        remove_button.setIcon(icon)
        remove_button.setIconSize(QtCore.QSize(16, 16))
        #remove_button.setFlat(True)
        remove_button.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        remove_button.clicked.connect(self._remove)

        vlayout.addWidget(remove_button)

        mlayout.addLayout(vlayout)

        self.setLayout(mlayout)

        browse_product_button.clicked.connect(self._browseProduct)
        self._product.textChanged.connect(self._updated)
        self._revisionType.currentIndexChanged.connect(self._updated)
        browse_source_button.clicked.connect(self._browseContainer)

        self._updateRevisionTypes()

    updated = QtCore.pyqtSignal()
    removed = QtCore.pyqtSignal(object)

    def cwd(self):
        return self._cwd
    def setCwd(self, cwd):
        self._cwd = cwd

    def product(self):
        return self._path, self._frameRange
    def setProduct(self, path, frame_range):
        self._path = path
        self._frameRange = frame_range

        if self._frameRange is not None:
            self._product.setText(self._path + "," + self._frameRange)
        else:
            self._product.setText(self._path)
        self._updateRevisionTypes()

    def container(self):
        return self._container
    def setContainer(self, container):
        self._container = container
        self._containerEdit.setText(str(container) if container is not None else "")
        self._updateRevisionTypes()

    def revisionType(self):
        return self._revisionType.currentRevisionType()
    def setRevisionType(self, revision_type):
        self._revisionType.setCurrentRevisionType(revision_type)

    @QtCore.pyqtSlot()
    def _updated(self):
        self.updated.emit()

    @QtCore.pyqtSlot()
    def _browseContainer(self):
        dlg = BrowserDialog(self, modal=True)
        dlg.setSelectedItem(self.container())
        dlg.setBrowseType(BrowserDialog.BrowseContainers)
        dlg.setHintText("Select the container.")
        if dlg.exec_() == QtGui.QDialog.Accepted:
            container = dlg.selectedItem()
            self.setContainer(container)

    @QtCore.pyqtSlot()
    def _browseProduct(self):
        dlg = QtGui.QFileDialog(self, "Product", self._cwd)
        dlg.setWindowTitle("Product...")
        dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
        dlg.setViewMode(QtGui.QFileDialog.Detail)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            filename = str(dlg.selectedFiles()[0])
            path = tank.util.sequence.get_pattern(filename)
            frame_range = tank.util.sequence.get_range(path, os.listdir(os.path.split(path)[0]))
            self.setProduct(path, frame_range)
            self.setCwd(os.path.split(self._path)[0])

    def _remove(self):
        self.removed.emit(self)

    def _updateRevisionTypes(self):
        valid_rts = [tank.find(rt) for rt in tank.list_revision_types()]

        # check for matching extension
        if self._path is not None:
            ext = os.path.splitext(self._path)[1].lstrip('.')
            try:
                valid_rts = [rt for rt in valid_rts if ext in rt.properties.extension_hint.split(',') \
                                                    or rt.properties.extension_hint is None]
            except:
                raise Exception("No extension hint found for revision type")

            # check for matching sequence vs. single file
            if self._frameRange is not None:
                resource_type = tank.constants.ResourceType.SEQUENCE
            else:
                if os.path.exists(self._path):
                    if os.path.isdir(self._path):
                        resource_type = tank.constants.ResourceType.FOLDER
                    else:
                        resource_type = tank.constants.ResourceType.SINGLE_FILE
                else:
                    resource_type = None

            valid_rts = [rt for rt in valid_rts if rt.properties.restrict_resource_type in (None, resource_type)]

        # check against container's valid revision types
        if self._container is not None:
            valid_rts = [rt for rt in valid_rts if rt in self._container.system.type.properties.valid_revision_types]

        valid_rts = sorted(valid_rts, key=lambda rt: rt.system.name)

        self._revisionType.setValidRevisionTypes([None] + valid_rts)

    def currentProduct(self):
        if self._frameRange == "":
            self._frameRange = None

        return {"path": self._path,
                "frame_range": self._frameRange,
                "container": self._container,
                "revision_type": self._revisionType.currentRevisionType()}

class ProductGroupListWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ProductGroupListWidget, self).__init__(parent)
        vlayout = QtGui.QVBoxLayout(margin=0)
        self.setLayout(vlayout)

        self._cwd = os.getcwd()
        self._container = None
        self._productGroups = []

        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtGui.QWidget()
        scroll_area.setWidget(scroll_widget)
        vlayout.addWidget(scroll_area)
        scroll_area.setFrameStyle(QtGui.QFrame.NoFrame)
        scroll_layout = QtGui.QVBoxLayout(margin=0)
        scroll_widget.setLayout(scroll_layout)

        sp = QtGui.QSizePolicy()
        sp.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        scroll_widget.setSizePolicy(sp)

        scroll_layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)

        add_button = QtGui.QPushButton()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        add_button.setIcon(icon)
        add_button.setIconSize(QtCore.QSize(16, 16))
        #add_button.setFlat(True)
        scroll_layout.addWidget(add_button)

        scroll_layout.addStretch()

        vlayout.addWidget(scroll_area)

        self._scrollLayout = scroll_layout
        self._scroll_area = scroll_area

        add_button.clicked.connect(self._addProductGroup)

        size = self.minimumSize()
        size.setHeight(200)
        self.setMinimumSize(size)

    def cwd(self):
        return self._cwd
    def setCwd(self, cwd):
        self._cwd = cwd

    def container(self):
        return self._container
    def setContainer(self, container):
        self._container = container

    @QtCore.pyqtSlot(ProductGroupWidget)
    def removeProductGroup(self, group):
        self._productGroups.remove(group)
        group.deleteLater()

    updated = QtCore.pyqtSignal()

    @QtCore.pyqtSlot()
    def _updated(self):
        self.updated.emit()

    def addProductGroup(self, path, frame_range=None, container=None, revision_type=None):
        product_group = ProductGroupWidget(self)
        product_group.setCwd(self._cwd)
        product_group.setProduct(path, frame_range)
        product_group.setContainer(container)
        product_group.setRevisionType(revision_type)
        product_group.removed.connect(self.removeProductGroup)
        product_group.updated.connect(self._updated)
        self._scrollLayout.insertWidget(len(self._productGroups), product_group)
        self._productGroups.append(product_group)

    @QtCore.pyqtSlot()
    def _addProductGroup(self):
        dlg = QtGui.QFileDialog(self, "Product", self._cwd)
        dlg.setWindowTitle("Product...")
        dlg.setFileMode(QtGui.QFileDialog.ExistingFiles)
        dlg.setViewMode(QtGui.QFileDialog.Detail)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            selection = set()
            for filename in dlg.selectedFiles():
                path = tank.util.sequence.get_pattern(str(filename))
                frame_range = tank.util.sequence.get_range(os.path.split(path)[1], os.listdir(os.path.split(path)[0]))
                selection.add((path, frame_range))

            for path, frame_range in selection:
                # consult the namer plugin for the container
                revision_type = plugins.get_one_namer().get_revision_type(self._container, path, frame_range)
                container = plugins.get_one_namer().get_container(self._container, self._container, revision_type, path)

                self.addProductGroup(path, frame_range, container, revision_type)

    def productGroups(self):
        return self._productGroups


class PublishDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        if parent is None:
            super(PublishDialog, self).__init__()
        else:
            super(PublishDialog, self).__init__(parent)

        self.setWindowTitle("Publish")

        self._sourceRevision = None

        vlayout = QtGui.QVBoxLayout()

        self._productGroupList = ProductGroupListWidget(self)
        vlayout.addWidget(self._productGroupList)

        groupbox = QtGui.QGroupBox("Source")
        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Revision:")
        hlayout.addWidget(label)
        self._source = QtGui.QLineEdit(enabled=False)
        browse_source_button = QtGui.QPushButton("Browse...")
        hlayout.addWidget(self._source)
        hlayout.addWidget(browse_source_button)
        groupbox.setLayout(hlayout)
        vlayout.addWidget(groupbox)

        groupbox = QtGui.QGroupBox("Description")
        hlayout = QtGui.QHBoxLayout()

        self._description = QtGui.QPlainTextEdit()
        sp = QtGui.QSizePolicy()
        sp.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        sp.setHorizontalStretch(0)
        sp.setVerticalPolicy(QtGui.QSizePolicy.Expanding)
        sp.setVerticalStretch(32)
        self._description.setSizePolicy(sp)
        hlayout.addWidget(self._description)
        groupbox.setLayout(hlayout)

        vlayout.addWidget(groupbox)

        self._buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
                                         QtCore.Qt.Horizontal)
        vlayout.addWidget(self._buttons)

        self.setLayout(vlayout)

        browse_source_button.clicked.connect(self._browseSource)
        self._buttons.accepted.connect(self.publish)
        self._buttons.rejected.connect(self.reject)

    def cwd(self):
        return self._productGroupList.cwd()
    def setCwd(self, cwd):
        self._productGroupList.setCwd(cwd)

    def container(self):
        return self._productGroupList.container()
    def setContainer(self, container):
        self._productGroupList.setContainer(container)

    def sourceRevision(self):
        return self._sourceRevision
    def setSourceRevision(self, revision):
        self._sourceRevision = revision
        self._source.setText(str(self._sourceRevision) if self._sourceRevision is not None else "")
        if revision is not None and self.container() is None:
            self.setContainer(revision.container)

    def addProduct(self, filename, container, revision_type):
        path = tank.util.sequence.get_pattern(filename)
        frame_range = tank.util.sequence.get_range(path, os.listdir(os.path.split(path)[0]))
        self._productGroupList.addProductGroup(path, frame_range, container, revision_type)

    def sizeHint(self): #IGNORE:R0201
        return QtCore.QSize(800, 300)

    @QtCore.pyqtSlot()
    def _browseSource(self):
        dlg = BrowserDialog(self, modal=True)
        dlg.setSelectedItem(self.container())
        dlg.setBrowseType(BrowserDialog.BrowseRevisions)
        dlg.setHintText("Select the source revision.")
        if dlg.exec_() == QtGui.QDialog.Accepted:
            revision = dlg.selectedItem()
            self.setSourceRevision(revision)

    @QtCore.pyqtSlot()
    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def publish(self):
        # publish the scene

        #progress = ProgressDialog(parent=self)
        #progress.setWindowTitle("Publish Progress")

        # we don't need to show the progress dialog. it will show itself after a few seconds

        description = str(self._description.document().toPlainText())

        for pg in self._productGroupList.productGroups():
            path, frame_range = pg.product()
            container = pg.container()
            revision_type = pg.revisionType()

            revision = container.create_revision(revision_type=revision_type)

            if frame_range is not None:
                revision.resource_type = tank.common.constants.ResourceType.SEQUENCE
                revision.publish_mode = tank.constants.PublishMode.MOVE
                revision.frame_range = frame_range

            revision.resource_path = path

            revision.properties.created_by = tank.util.misc.resolve_current_user()
            revision.properties.description = description
            if self._sourceRevision is not None:
                revision.properties.sources = [self._sourceRevision]

            # tank callbacks
            #for cb in ("on_progress_change", "should_abort", "did_abort", "on_error"):
            #    if hasattr(progress, cb):
            #        publisher.add_callback(cb, getattr(progress, cb))

            #if hasattr(progress, "on_publish"):
            #    progress.on_publish(revision_type.get_address(),
            #                        container.get_address(),
            #                        path)

            # do it

            # TODO: temporary, see the exception handler
            import psycopg2

            try:
                revision.save(force_change=True)
                print "Published " + str(revision)
            except psycopg2.InterfaceError:
                # WORKAROUND FOR psycopg2.InterfaceError caused by bug in tank
                for r in tank.get_children(revision_type, filters=["container is %s" % container.system.address, "seal_date is none"]).fetch_all():
                    r.server_object().seal()
            except Exception, e:
                import traceback
                traceback.print_exc()
                QtGui.QMessageBox.critical(None, "Publish failed!", str(e))

        self.close()
