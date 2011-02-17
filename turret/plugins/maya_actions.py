from turret.tankscene import Action
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

def get_actions(node, actions):
    if isinstance(node.data, MayaNodeData):
        actions["frame"] = Action("Frame Objects", func=frame_objects, args=[node])
        actions["select"] = Action("Select Objects", func=select_objects, args=[node])

    return actions

def select_objects(node):
    assert isinstance(node.data, MayaNodeData)
    node.data.select()

def frame_objects(node):
    assert isinstance(node.data, MayaNodeData)
    node.data.frame()
