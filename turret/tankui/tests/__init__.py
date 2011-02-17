"""
Setup and teardown for turret tests.
"""

import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import tank

from turret.tests.test_tankscene import SceneTestBase

app = QApplication(sys.argv)

class UITestBase(SceneTestBase):
    def setup(self):
        super(UITestBase, self).setup()
        self.app = app
    
    def teardown(self):
        super(UITestBase, self).teardown()

