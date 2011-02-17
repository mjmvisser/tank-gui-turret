"""
Generic action plugin. This delegate is never used and only
exists as a description of the action plugin interface.
Actions are responsible for modifying the state of the host application
or the tankscene. A single plugin can define multiple actions.
"""

from turret.tankscene import Action, Param

def get_actions(node, actions):
    """Returns a dictionary of actions supported by node, or None."""
    if False:
        actions["action1"] = Action("Do something!", sample1, node)
        actions["action2"] = Action("Do something else", sample2, node,
                                    params=[Param("revision", Param.Revision, default=node.revision)])
    return actions

def sample1(node):
    """Called when "action1" is invoked. node is the tankscene node."""
    pass

def sample2(node, revision):
    """Called when "action2" is invoked. node is the tankscene node, revision is the revision parameter."""
    pass
