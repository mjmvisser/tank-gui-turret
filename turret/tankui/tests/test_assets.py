import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from turret.tankui.assets import AssetsWindow

from . import UITestBase

class TestAssets(UITestBase):
    def setup(self):
        super(TestAssets, self).setup()

    def teardown(self):
        super(TestAssets, self).teardown()

    def test_assets(self):
        dlg = AssetsWindow(self._scene)
        assert dlg.exec_() == QDialog.Accepted
