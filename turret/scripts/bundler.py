import sys, os
from optparse import OptionParser
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from turret.tankui.bundler import BundlerWindow

from turret import plugins
plugins.initialize()


if __name__ == "__main__":
    usage="publish [options] [file]"

    app = QApplication(sys.argv)

    parser = OptionParser(usage=usage)

    options, args = parser.parse_args()

    if len(args) > 1:
        parser.error("Please specify a single bundle file")
    else:
        if len(args) == 1:
            path = os.path.abspath(args[0]).replace("/dfs1/net", "")
        else:
            path = None

    window = BundlerWindow()
    
    window.show()
    
    app.exec_()
