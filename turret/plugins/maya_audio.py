from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="MayaAudio",
                                   attrib_name="filename",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        # create a new audio node with our name
        return pm.createNode("audio", name=self.name)

def supports_ext(ext):
    return ext in (".aif", ".aiff", ".wav")

def get_dependencies(parent):
    return [Data(node=node) for node in pm.ls(type="audio") if node in parent.child_nodes and node.filename.get() != ""]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)

