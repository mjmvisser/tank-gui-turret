import os, shutil
import tank
from turret.tankscene import Action, Param
from turret import sandbox

def get_actions(node, actions):
    """Returns a dictionary of actions supported by node, or None."""
    # checkout
    if node.is_revision() and hasattr(node.data, "update") \
            and node.revision.resource_type == tank.constants.ResourceType.SINGLE_FILE:
        # we can only do a checkout if the delegate supports updates
        # don't try to check out sequences
        actions["checkout"] = Action("Check-out", func=checkout, args=[node])

    # import
    if hasattr(node.data, "import_"):
        # we can only do an import if the delegate supports imports
        actions["import"] = Action("Import", func=node.import_)

    if hasattr(node.data, "update"):
        # we can only do a replace if the delegate supports updates
        actions["replace"] = Action("Replace...", func=replace, args=[node],
                                    params=[Param("revision", Param.Revision,
                                                  label="Revision",
                                                  default=(node.revision if node is not None else None))])

    if hasattr(node.data, "update") and node.is_revision() and node.container.latest_revisions.has_key(node.revision.system.type.system.name) and node.revision != node.container.latest_revisions[node.revision.system.type.system.name]:
        actions["latest"] = Action("Update to Latest",
                                   func=replace_with_latest, args=[node])
#        actions["recommended"] = Action("Update to Recommended",
#                                        func=replace_with_recommended, args=[node])

    if hasattr(node.data, "update") and node.container and node.container.system.type.properties.use_name:
        actions["container_name_to_filename"] = Action("Set Container Name to Filename",
                                                       func=set_container_name_to_filename, args=[node])

    if node.is_working():
        params = [Param("description", Param.Text, label="Description", default=""),
                  Param("subset", Param.NodeList, label="Nodes", default=(), node=node)]
        try:
            if node.revision_type is not None:
                for field_name, field in node.revision_type.fields.items():
                    try:
                        if field.properties.hints['set_at_publish']:
                            if field.properties.type == "boolean":
                                p = Param(field_name, Param.Boolean, label=field.properties.nice_name, default=False)
                                params.append(p)
                    except (TypeError, KeyError):
                        pass
        except:
            import traceback
            print traceback.print_exc()

#        if os.getenv('TOOLSET') not in ('beta', 'dev'):
        if os.getenv('TOOLSET') != 'dev':
            # Disable publish when a dev or beta toolset is used.
            actions["publish"] = Action("Publish...", func=publish, args=[node], params=params)

    return actions

def checkout(node):
    """
    Makes a local copy of this node's data in the working directory and
    schedules an update of the delegate.
    """
    # we can only do a checkout if the delegate allows updates
    assert node.is_revision() and hasattr(node.data, "update")

    # get the working path for the revision
    work_path = sandbox.get_path(node.revision, node.scene.container)

    # make directories
    work_dir = os.path.split(work_path)[0]

    if not os.path.exists(work_dir) or not os.path.isdir(work_dir):
        os.makedirs(work_dir)

    # do the copy
    shutil.copy(node.data.path, work_path)

    # set correct permissions
    # there doesn't appear to be a way to simply ignore the source permissions during the copy
    # TODO: there is no way to get the umask without setting it?
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(work_path, 0666 & ~umask)

    # clear the revision
    node.revision = None

    # update the delegate data and trigger an update with reload
    node.set_path(work_path, reload=True)

def replace(node, revision):
    assert hasattr(node.data, "update")
    node.set_revision(revision, reload=True)

def replace_with_latest(node):
    # we can only do a latest or recommended if the delegate supports updates and we
    # are a revision
    assert hasattr(node.data, "update")
    try:
        latest = node.container.latest_revisions[node.revision.system.type.system.name]
        node.set_revision(latest, reload=True)
    except tank.common.TankNotFound:
        pass

def set_container_name_to_filename(node):
    # extract the filename
    node.name = os.path.splitext(os.path.split(node.data.path)[1])[0]
    node.update()

def publish(node, description, subset, **kwargs):
    node.publish(description, subset=subset, properties=kwargs)