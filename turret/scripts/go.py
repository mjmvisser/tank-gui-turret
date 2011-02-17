import sys, os, errno
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import tank
from turret.tankui.browser import BrowserDialog
from turret import sandbox, plugins

plugins.initialize()

app = QApplication([])

app.setOrganizationName("LumiereVFX")
app.setOrganizationDomain("lumierevfx.com")
app.setApplicationName("turret")

current_container = sandbox.get(os.getcwd())

dialog = BrowserDialog(modal=True)
dialog.setBrowseType(BrowserDialog.BrowseContainers)
dialog.setHintText("Select a container.")
dialog.setCwd(os.getcwd())
dialog.setSelectedItem(current_container)

path = os.getcwd()
if dialog.exec_() == QDialog.Accepted:
    container = dialog.selectedItem()

    if container:
        work_root = sandbox.get_path(container)
        if work_root is not None:
            path = work_root

print path