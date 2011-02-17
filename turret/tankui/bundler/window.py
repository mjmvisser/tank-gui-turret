import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from ... import sandbox, plugins
from ..browser import BrowserDialog
from ...tankscene import Scene

from .ui_bundler import Ui_BundlerWindow

class BundlerWindow(QMainWindow, Ui_BundlerWindow):
    def __init__(self, parent=None, **kwargs):
        if parent is not None:
            super(BundlerWindow, self).__init__(parent, **kwargs)
        else:
            super(BundlerWindow, self).__init__(**kwargs)

        self.setupUi(self)

        self._assetsWindow.setAttribute(Qt.WA_DeleteOnClose)
        self._assetsWindow.destroyed.connect(self.close)

        self._newBundleAction.triggered.connect(self._newBundle)
        self._openBundleAction.triggered.connect(self._openBundle)
        self._saveBundleAction.triggered.connect(self._saveBundle)
        self._saveBundleAsAction.triggered.connect(self._saveBundleAs)
        self._setProjectAction.triggered.connect(self._setProject)

        self._newBundle()

    def _newBundle(self):
        scene_delegate = plugins.get_one_delegate(name="bundler_bundle")
        scene = Scene(scene_delegate)
        self._assetsWindow.setScene(scene)

    def _openBundle(self):
        bundle_filename = QFileDialog.getOpenFileName(self, "Open Bundle", os.getcwd(), "Bundle Files (*.bundle)")
        if len(bundle_filename) > 0:
            scene_delegate = plugins.get_one_delegate(name="bundler_bundle")
            scene = Scene(scene_delegate, bundle_filename)
            self._assetsWindow.setScene(scene)

    def _saveBundle(self):
        self._assetsWindow.scene().save()

    def _saveBundleAs(self):
        bundle_filename = QFileDialog.getSaveFileName(self, "Save Bundle As", os.getcwd(), "Bundle Files (*.bundle)")
        if bundle_filename is not None:
            self._assetsWindow.scene().path = bundle_filename
            self._assetsWindow.scene().save()

    def _setProject(self):
        try:
            container = sandbox.get(os.getcwd())[0]
        except:
            container = None

        dialog = BrowserDialog(self, modal=True)
        dialog.setBrowseType(BrowserDialog.BrowseContainers)
        dialog.setHintText("Select a container.")
        dialog.setSelectedItem(container)

        if dialog.exec_() == QDialog.Accepted:
            container = dialog.selectedItem()

            if not container:
                return

            work_root = sandbox.get_path(container)

            # create the directory
            if not os.path.exists(work_root):
                os.makedirs(work_root)

            # create subdirectory
            if not os.path.exists(os.path.join(work_root, "bundles")):
                os.makedirs(os.path.join(work_root, "bundles"))

            # cd
            os.chdir(work_root)

            self._assetsWindow.refresh()
            # TODO: status bar
            #print "Set project to %s" % work_root

