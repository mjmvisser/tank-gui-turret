import sys, os, re
import tank

if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    # monkeypatch python 2.5 to include os.path.relpath
    def relpath(path, start='.'):
        sep = '/'
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        start_list = os.path.abspath(start).split(sep)
        path_list = os.path.abspath(path).split(sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))

        rel_list = ['.'] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return "."
        return os.path.join(*rel_list)

    os.path.relpath = relpath


class NotWorkingPathError(Exception):
    pass

class UnmappedVFSPath(Exception):
    pass

#
# For simplicity, work directories look like this:
# /prod/proj/work/sequences/00/shots/00_0100/anim.markv/{scenes,images,etc}
#

def get_path(obj, base=None):
    if isinstance(obj, tank.TankContainer):
        return _get_container_path(obj, base)
    elif isinstance(obj, tank.TankRevision):
        return _get_revision_path(obj, base)
    else:
        return None

def _get_container_path(container, base=None):
    assert isinstance(container, tank.TankContainer)

    # TODO: check for IndexError and throw a more meaningful error ("obj is not mapped in vfs")
    try:
        partial_path = container.system.vfs_paths[0]
    except IndexError:
        raise UnmappedVFSPath("%s has no vfs paths mapped" % str(container))

    if base is not None:
        try:
            base_partial_path = base.system.vfs_paths[0]
        except IndexError:
            raise UnmappedVFSPath("%s has no vfs paths mapped" % str(base))

        # ignore pylint; os.path.relpath is monkeypatched above for Python < 2.6
        subdirs = os.path.relpath(partial_path, base_partial_path)  #@UndefinedVariable
        if subdirs == ".":
            subdirs = None
    else:
        subdirs = None

    # remove the trailing subdir (i.e. scenes)
    if subdirs is not None and partial_path[-len(subdirs):] == subdirs:
        partial_path = partial_path[0:-len(subdirs)]

    # remove the leading and trailing "/" so os.path.join doesn't discard prior paths
    partial_path = partial_path.strip("/")

    # TODO: get this from tank config
    container_path = os.path.join("/prod", os.environ["TANK_PROJECT"].lower(), "work", partial_path+"." + os.environ["USER"])

    if subdirs is not None:
        container_path = os.path.join(container_path, subdirs)

    return container_path

def _get_revision_path(revision, base=None):
    # first, grab the container path. it will look like:
    #  /prod/soe/work/assets/test/test/model.markv/blah
    container_path = _get_container_path(revision.container, base)

    # now, grab the partial revision path. this looks something like:
    #  assets/test/test/model/scenes/test_model_v001-1451_11.mb
    try:
        partial_revision_path = revision.system.vfs_paths[0].lstrip('/')
    except IndexError:
        raise UnmappedVFSPath("%s has no vfs paths mapped" % str(revision))

    # also grab the partial container path. this looks like:
    # assets/test/test/model
    try:
        partial_container_path = revision.container.system.vfs_paths[0].lstrip('/')
    except IndexError:
        raise UnmappedVFSPath("%s has no vfs paths mapped" % str(revision.container))

    # now remove the partial container path from the partial revision path
    # ignore pylint; os.path.relpath is monkeypatched above for Python < 2.6
    revision_path = os.path.join(container_path, os.path.relpath(partial_revision_path, partial_container_path)) #@UndefinedVariable

    #strip out the version and id strings
    revision_path = re.sub(r"_v[0-9]+-[0-9]+_[0-9]+", "", revision_path)

    return revision_path

def get(work_path):
    """Returns container, revision_type associated with the work path."""
    # if it's a revision, it's definitely not a working path
    # TODO: get from tank config
    if work_path[0:5] == "/tank":
        raise NotWorkingPathError("%s is not a working path." % work_path)

    dir = None
    filename = None
    ext = None
    resource_type = None

    if os.path.isdir(work_path):
        dir = work_path
    elif os.path.isfile(work_path):
        dir, filename = os.path.split(work_path)
        filename, ext = os.path.splitext(filename)
        resource_type = tank.common.constants.ResourceType.SINGLE_FILE
    else:
        # strip off names until we find a directory that exists
        ext = os.path.splitext(work_path)[1]
        partial_path = work_path
        while partial_path not in ("/", ""):
            if os.path.isdir(partial_path):
                dir = partial_path
                break
            partial_path = os.path.split(partial_path)[0]

    # bail, can't parse
    if dir is None:
        raise NotWorkingPathError("%s is not a working path." % work_path)

    # TODO: more hard-coded values
    partial_path = dir.replace("/dfs1/net", "").replace("/prod/" + os.environ["TANK_PROJECT"].lower() + "/work", "")
    partial_path = re.sub(r"(.*?)([.][^/]*)(.*)", r"\1\3", partial_path)

    # iterate over the path, stripping the final directory off each time until we find a match
    container = None
    while partial_path != "/":
        try:
            container = tank.find(partial_path)
            break
        except:
            pass
        partial_path = os.path.split(partial_path)[0]

    if container is not None or ext is not None or resource_type is not None:
        # identify the revision type
        revision_type = _get_revision_type(container, ext, resource_type)
    else:
        revision_type = None

    return container, revision_type

def get_root_dir():
    # TODO: hard-coded values
    return os.path.join("/prod", os.environ["TANK_PROJECT"].lower(), "work")

def _get_revision_type(container, ext, resource_type):
    # check for valid revision types
    if container is not None:
        # TODO: container.system.type_object returns a local API object
        valid_rts = container.system.type.properties.valid_revision_types

    if container is None or len(valid_rts) == 0:
        valid_rts = [tank.find(t) for t in tank.list_revision_types()]

    # check for matching extension
    if ext is not None:
        valid_rts = [rt for rt in valid_rts if rt.properties.has_key("extension_hint") and rt.properties.extension_hint is not None and ext.lstrip('.') in rt.properties.extension_hint.split(',')]

    # check for matching resource type
    if resource_type is not None:
        valid_rts = [rt for rt in valid_rts if rt.properties.restrict_resource_type in (resource_type, None)]

    # return the first match or None
    try:
        return valid_rts[0]
    except IndexError:
        return None

