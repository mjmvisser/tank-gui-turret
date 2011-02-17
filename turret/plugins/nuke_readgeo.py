from turret.plugins import UnsupportedPluginError

try:
    import nuke
    from turret.nukeutils import NukeNodeData, SUPPORTED_GEO_EXTS
except ImportError:
    raise UnsupportedPluginError()

class Data(NukeNodeData):
    def __init__(self, name=None, path=None, frame_range=None, node=None):
        super(Data, self).__init__(dtype="NukeReadGeo",
                                   node_type=nuke.nodes.ReadGeo,
                                   knob_name="file",
                                   name=name,
                                   path=path,
                                   frame_range=frame_range,
                                   node=node)

def supports_ext(ext):
    return ext in SUPPORTED_GEO_EXTS 

def get_dependencies(parent):
    if parent.type == "NukeScript":
        return [Data(node=node) for node in nuke.root().nodes() if node.Class() == "ReadGeo"]
    else:
        return []

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path, frame_range=frame_range)

#