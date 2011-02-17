from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

# requires the 3delight plugin
mayaVersion = pm.about(version=True).split()[0]
plugin = '3delight_for_maya' + mayaVersion
if not pm.pluginInfo(plugin, query=True, loaded=True):
    raise UnsupportedPluginError()


class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="DLRibArchive",
                                   attrib_name="ribFilename",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        raise NotImplementedError("To be done")


def supports_ext(ext):
    return ext == ".rib"

def get_dependencies(parent):
    # find all rib archive nodes
    return [Data(node=node) for node in pm.ls(type="delightRibArchive") if node in parent.child_nodes]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)
