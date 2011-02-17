import os, re

import pymel.core as pm

#if sys.version_info[0] == 2 and sys.version_info[1] < 7:
#    from pythonutils.odict import OrderedDict

class GeocacheError(BaseException):
    pass

class MayaNodeData(object):
    def __init__(self, type, attrib_name=None, name=None, path=None, node=None):
        self.type = type
        self._attrib_name = attrib_name
        self.name = name
        self.path = path
        self.node = node
        self.revision_type_id = None
        self.container_id = None
        self.last_revision_id = None
        self.child_nodes = []

        if self._attrib_name is not None:
            safe_attrib_name = re.sub(r"\[|\]", "", attrib_name)
            self._container_id_attrib_name = "__container__" + safe_attrib_name
            self._revision_type_id_attrib_name = "__revisionType__" + safe_attrib_name
            self._last_revision_id_attrib_name = "__lastRevision__" + safe_attrib_name
        else:
            self._container_id_attrib_name = "__container"
            self._revision_type_id_attrib_name = "__revisionType"
            self._last_revision_id_attrib_name = "__lastRevision"

        # read the relevant attributes
        # container and revision id
        self._readIds()
        # node name
        self._readName()
        # path
        self._readPath()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def _readIds(self):
        if self.node is not None:
            if self.node.hasAttr(self._container_id_attrib_name):
                self.container_id = self.node.attr(self._container_id_attrib_name).get()
            if self.node.hasAttr(self._revision_type_id_attrib_name):
                self.revision_type_id = self.node.attr(self._revision_type_id_attrib_name).get()
            if self.node.hasAttr(self._last_revision_id_attrib_name):
                self.last_revision_id = self.node.attr(self._last_revision_id_attrib_name).get()

    def _readName(self):
        if self.node is not None:
            self.name = self.node.name()

    def _readPath(self):
        if self.node is not None:
            path = self.node.attr(self._attrib_name).get()

            # check if it's relative, and if so, make it absolute using the project dir
            if os.path.isabs(path):
                self.path = path
            else:
                self.path = os.path.join(pm.workspace.path, path)

    def _writeIds(self):
        if self.node is not None:
            locked = self.node.isLocked()
            try:
                if locked:
                    self.node.unlock()

                # create attributes on the node (if they don't already exist) and we have them on self
                # remove them if they do, but we don't
                for attrib_name, id_name in zip((self._container_id_attrib_name,
                                                 self._revision_type_id_attrib_name,
                                                 self._last_revision_id_attrib_name),
                                                ("container_id",
                                                 "revision_type_id",
                                                 "last_revision_id")):
                    self._writeId(attrib_name, id_name)
            finally:
                if locked:
                    self.node.lock()

    def _writeId(self, attrib_name, id_name):
        value = getattr(self, id_name, None)
        if value is not None:
            if not self.node.hasAttr(attrib_name):
                self.node.addAttr(attrib_name, dataType="string", hidden=True)
            attrib = self.node.attr(attrib_name)
            if attrib.isLocked():
                attrib.unlock()
            attrib.set(value, type="string")
        else:
            if self.node.hasAttr(attrib_name):
                attrib = self.node.attr(attrib_name)
                if attrib.isLocked():
                    attrib.unlock()
                attrib.delete()

    def _writeName(self):
        if self.node is not None:
            if self.node.name != self.name:
                self.node.rename(self.name)


    def _writePath(self, reload):
        if self.node is not None:
            attrib = self.node.attr(self._attrib_name)
            if attrib.get() != self.path:
                locked = attrib.isLocked()
                if locked:
                    attrib.unlock()
                attrib.set(self.path)
                if locked:
                    attrib.lock()

    def _createNode(self):
        raise NotImplementedError("This class does not support node creation.")

    def _deleteNode(self):
        pm.general.delete(self.node.node())

    @property
    def children(self):
        return ()

    def update(self, reload):
        if self.node is None:
            # create a new node with our name and path
            self.node = self._createNode()

        # write ids, node name and path
        self._writeIds()
        self._writeName()
        self._writePath(reload)

    def remove(self):
        if self.node is not None:
            self._deleteNode()
            self.revision_type_id = None
            self.container_id = None
            self.name = None
            self.path = None

    def select(self):
        if self.node is not None:
            pm.select(self.node)

    def frame(self):
        if self.node is not None:
            # save selection
            sel = pm.selectedNodes()
            # select and frame
            self.select()
            pm.runtime.FrameSelectedInAllViews()
            # restore selection
            pm.select(sel)

def setProject(path):
    # create the directory
    if not os.path.exists(path):
        os.makedirs(path, 0775)

    # set maya project (using the pymel "workspace" command fails, so use the mel command)
    pm.mel.setProject(path)

    # set sane file rules
    pm.workspace.fileRules["scene"] = "scenes"
    pm.workspace.fileRules["mayaAscii"] = "scenes"
    pm.workspace.fileRules["mayaBinary"] = "scenes"
    pm.workspace.fileRules["animExport"] = ""
    pm.workspace.fileRules["animImport"] = ""
    pm.workspace.fileRules["IGES"] = "data"
    pm.workspace.fileRules["DXFexport"] = "data"
    pm.workspace.fileRules["OBJexport"] = "data"
    pm.workspace.fileRules["lights"] = "renderData/shaders"
    pm.workspace.fileRules["mel"] = "mel"
    pm.workspace.fileRules["particles"] = "particles"
    pm.workspace.fileRules["audio"] = "sound"
    pm.workspace.fileRules["RIBexport"] = "data"
    pm.workspace.fileRules["RIB"] = "data"
    pm.workspace.fileRules["depth"] = "renderData/depth"
    pm.workspace.fileRules["diskCache"] = "data"
    pm.workspace.fileRules["sourceImages"] = "sourceimages"
    pm.workspace.fileRules["iprImages"] = "renderData/iprImages"
    pm.workspace.fileRules["textures"] = "textures"
    pm.workspace.fileRules["aliasWire"] = "data"
    pm.workspace.fileRules["move"] = "data"
    pm.workspace.fileRules["renderScenes"] = "renderScenes"
    pm.workspace.fileRules["images"] = "images"
    pm.workspace.fileRules["DXF"] = "data"
    pm.workspace.fileRules["clips"] = "clips"
    pm.workspace.fileRules["OBJ"] = "data"
    pm.workspace.fileRules["templates"] = "assets"

    for dir in pm.workspace.fileRules.values():
        path = os.path.join(pm.workspace.path, dir)
        if not os.path.exists(path):
            os.makedirs(path, 0755)

