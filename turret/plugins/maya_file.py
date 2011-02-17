from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="MayaFile",
                                   attrib_name="fileTextureName",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        # create a new File node with our name and path
        # need to call shadingNode, as the File constructor calls createNode instead of shadingNode
        # this results in a node that can't be seen in the hypershade
        return pm.shadingNode("file", name=self.name, asTexture=True)

def supports_ext(ext):
    return ext in (".jpg", ".jpeg", ".tif", ".tiff", ".sgi", ".hdr", ".tdl", ".iff", ".rgb")

def get_dependencies(parent):
    return [Data(node=node) for node in pm.ls(type="file") if node in parent.child_nodes and node.fileTextureName.get() != ""]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)

