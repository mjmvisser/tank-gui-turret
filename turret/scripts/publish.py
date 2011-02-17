#!/bin/env python

import sys, os
from optparse import OptionParser
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import turret
from turret.tankui.publish import PublishDialog

import tank


if __name__ == "__main__":
    usage="publish [options] [file]"

    app = QApplication(sys.argv)

    parser = OptionParser(usage=usage)

    parser.add_option("-t", "--type", dest="revision_type",  metavar="REVISION_TYPE", default=None,
                      help="publish this type of revision, e.g. MayaScene")
    parser.add_option("-c", "--container", dest="container",  metavar="CONTAINER", default=None,
                      help="publish to this container, e.g. Rig(AssetType(dinosaur), Asset(trex), RigType(skin))")
    parser.add_option("-s", "--source", dest="source_revision", metavar="REVISION", default=None,
                      help="(optional) the given revision is the source of the file")

    options, args = parser.parse_args()

    if len(args) > 1:
        parser.error("Please specify a single file to publish")
    else:
        if len(args) == 1:
            path = os.path.abspath(args[0]).replace("/dfs1/net", "")
        else:
            path = None

    revision_type = tank.find(options.revision_type) if options.revision_type is not None else None
    container = tank.find(options.container) if options.container is not None else None
    source_revision = tank.find(options.source_revision) if options.source_revision is not None else None

    turret.plugins.initialize()

    dialog = PublishDialog()

    if path is not None:
        dialog.addProduct(path, container, revision_type)

    dialog.setSourceRevision(source_revision)

    dialog.show()

    app.exec_()
