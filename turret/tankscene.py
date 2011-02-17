"""
This module provides a high-level scene graph decoupled from any particular software.
It uses registered delegate plugins (see @module plugins) to inspect a scene and builds a
simple dependency graph suitable for use by a QAbstractItemModel.

A dependency graph can be constructed like this:
    scene = Scene.Scene(delegate, path)
"""

import os, re, sys
from functools import partial
import tank
import plugins
import sandbox

if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    # monkeypatch python 2.5 to include os.path.relpath
    def relpath(path, start='.'):
        """Return a relative version of a path"""
        sep = '/'

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


__all__ = ["InvalidNodeError",
           "Scene",
           "Dependency",
           "Param",
           "Action",
           "ActionError"]


class Param(object):
    Text = "text"
    Boolean = "bool"
    Integer = "int"
    Revision = "revision"
    Container = "container"
    Version = "version"
    RevisionList = "revisionlist"
    NodeList = "nodelist"

    """
    A parameter to an action. A parameter has a name, a type, and a value.
    Optionally, it may also have a label, for UI purposes.
    """
    def __init__(self, name, type, label=None, default=None, node=None):
        self.name = name
        self.type = type
        self.label = label
        self.value = default
        self.node = node


class ActionError(Exception):
    pass


class Action(object):
    """
    Fully describes an action and how to perform (execute) it. An action has
    a name, a callable, and a set of parameters. Parameters can be filled in
    after the action has been created.
    """
    def __init__(self, name, func, params=[], args=[], kwargs={}):
        assert isinstance(name, str), name
        assert callable(func), func
        assert all(isinstance(p, Param) for p in params), params

        self._name = name
        # bind args and kwargs to the function
        self.func = partial(func, *args, **kwargs)
        self.params = params

    def is_valid(self):
        return self.func is not None

    @property
    def name(self):
        """The action name (str)."""
        return self._name

    def execute(self):
        """Calls the action's function with the parameter values."""
        # call our action
        if self.func is not None:
            return self.func(**dict((p.name, p.value) for p in self.params))


class InvalidNodeError(Exception):
    def __init__(self, node, msg):
        super(InvalidNodeError, self).__init__(node + ": " + msg)


class UncommittedChangesError(Exception):
    def __init__(self, node):
        super(UncommittedChangesError, self).__init__("The '%s' node has uncommitted changes" % node.node)

class NoVFSRuleError(Exception):
    def __init__(self, revision):
        super(NoVFSRuleError, self).__init__("The revision '%s' has no matching VFS rule" % str(revision))

class NonUniqueWorkingContainerError(Exception):
    def __init__(self, nodes, container):
        super(NonUniqueWorkingContainerError, self).__init__("Working nodes '%s' are using the same container '%s'" % (', '.join(n.node for n in nodes), str(container)))

def _get_label_types(container_type):
    """
    Returns the label types associated with a container type.

    :param container_type: The container type.
    :type limit: tank.local.EntityType
    :rtype: list of tank.local.EntityTypes (label types)
    """
    assert isinstance(container_type, tank.TankType), container_type
    assert container_type.properties.container_type == tank.constants.ContainerType.CONTAINER, container_type.properties.container_type

    # TODO: find the constants for "label" and "Entity Type"
    label_types = [tank.find(field.properties.validation["address"]) \
                       for field in container_type.fields.values() \
                           if field.properties.type == "label" and \
                              field.properties.validation["type"] == "Entity Type"]

    return sorted(label_types, key=lambda lt: lt.system.name)


class Node(object):
    """
    The base class of all scene graph nodes. This is an abstract type,
    and should not be constructed. Please use one of the derived classes instead.
    """
    def __init__(self, delegate, data, parent=None):
        """
        Creates a new Node object. Nodes have a parent (None for the root object)
        and children (stored as lists in the dependencies' properties).
        Children are generated automatically by querying the node's delegate.

        :param delegate: The :mod:`delegate <turret.delegates>` for this node.
        :param data: Blind data object created by the delegate.
        :param parent: Parent node object.
        :type parent: Node
        """
        self._data = data
        self._parent = parent
        self._delegate = delegate

        # settable properties
        self._container = None
        self._container_type = None
        self._labels = None
        self._revision = None
        self._revision_type = None
        self._name = None
        self._version = None
        self._actions = None
        self._pending_action = None

        # list of source revisions handled by get/set_sources (.sources property)
        self._sources = []

        # determine if it's a valid work scene or a revision and set
        # revision, revision type, container, container type, and labels
        try:
            # TODO: temporary until Tm handles sequences properly
            path = re.sub(r"(.*[.]seq)(.*)", r"\1", self._data.path)

            # it's a revision
            self._revision = tank.find(path)
            self._update_revision_properties()
        except:
            # FIXME: catch only the "not found" exception!
            # the TransformManager could not map the path to a revision.
            # See if it's a sandbox location.
            try:
                self._revision = None
                self._version = None
                self._container, self._revision_type = sandbox.get(self._data.path)

                if self._container is not None:
                    self._update_container_properties()
                else:
                    # not sure if we end up here
                    pass
            except:
                # neither revision nor valid working
                pass

        # read the container from the data, if available
        if self._revision is None and hasattr(self._data, "container_id") and self._data.container_id is not None:
            try:
                self._container = tank.find(str(self._data.container_id))
                # invalidate
                self._container_type = None
                self._labels = None
                self._name = None
                self._update_container_properties()
            except:
                pass

        # if we have no revision, read the revision type from the data
        if self._revision is None and hasattr(self._data, "revision_type_id") and self._data.revision_type_id is not None:
            try:
                self._revision_type = tank.find(str(self._data.revision_type_id))
                # invalidate
                self._revision = None
                self._update_container_properties()
            except:
                pass

        # if we still have no revision type set, use the first available
        if self._revision_type is None and len(self.valid_revision_types) >  1:
            self._revision_type = self.valid_revision_types[1]

        # we have a container type
        #if self.is_working() and self._container_type is not None:
        #    # delegate to the namer to suggest alternate labels and/or name
        #    self.labels = plugins.get_one_namer().get_labels(self._parent._container if self._parent is not None else None, self._container, self._revision_type, self._data.path)
        #    self.name = plugins.get_one_namer().get_name(self._parent._container if self._parent is not None else None, self._name, self._labels, self._revision_type, self._data.path)

        # child dependencies
        all_dependencies = [Dependency(delegate, data, self) \
                                for delegate in plugins.get_delegates(attrs=("get_dependencies",)) \
                                    for data in delegate.get_dependencies(self._data)]

        # filter out dependencies that are a child of another dependency
        self._dependencies = list(set(d1 for d1 in all_dependencies for d2 in all_dependencies if not hasattr(d2, "child_nodes") or d1.node not in d2.child_nodes))

    @property
    def data(self):
        return self._data

    @property
    def delegate(self):
        return self._delegate

    # property
    def get_revision(self):
        """
        Returns the revision address in the form rev(ver, container([name, ]label1, label2, ...)).

        :rtype: string
        """
        return self._revision
    def set_revision(self, r, reload=True):
        assert r is None or isinstance(r, tank.TankRevision), r
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if self._revision != r:
            self._revision = r
            self._revision_type = None
            self._version = None
            self._sources = ()
            self._actions = None
            self.update(reload=reload)
    revision = property(get_revision, set_revision)

    # property
    def get_sources(self):
        return self._sources
    def set_sources(self, sources):
        assert all(isinstance(s, tank.TankRevision) for s in sources), sources
        if self._sources != sources:
            self._sources = sources
            # no update required
    sources = property(get_sources, set_sources)

    # property
    def get_node(self):
        """
        Returns the node name.

        :rtype: string
        """
        return self._data.name
    def set_node(self, node):
        assert isinstance(node, str), node
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if self._data.name != node:
            self._data.name = node
            self.update()
    node = property(get_node, set_node)

    # property
    def get_revision_type(self):
        """
        Returns the revision type address.

        :rtype: string or None
        """
        return self._revision_type
    def set_revision_type(self, rt):
        assert (isinstance(rt, tank.TankType) and rt.properties.container_type == tank.constants.ContainerType.REVISION) or rt is None, rt
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if self._revision_type != rt:
            self._revision_type = rt
            # invalidate
            self._revision = None
            self._actions = None
            self.update()
            # cascade the change to any nodes in the scene with the same path
            self.scene.set_revision_type_by_path(self.path, self._revision_type)
    revision_type = property(get_revision_type, set_revision_type)

    def set_revision_type_by_path(self, path, revision_type):
        """
        Sets the revision type if the given path matches.
        Recurses on working dependencies.
        """
        if self.is_working() and self.path == path:
            self.revision_type = revision_type

        for d in self.dependencies:
            d.set_revision_type_by_path(path, revision_type)


    @property
    def valid_revision_types(self):
        """
        Returns the list of valid revision types. Types are filtered against the extension_hint and
        restrict_resource_type properties of the revision type and the valid_revision_types property
        of the container. The first entry is always None.

        :rtype: list of strings
        """
        # check for valid revision types
        # TODO: simplify when list_* returns types instead of strings
        valid_rts = [tank.find(rt) for rt in tank.list_revision_types()]

        # check for matching extension
        if isinstance(self._data.path, basestring):
            ext = os.path.splitext(self._data.path)[1].lstrip('.')
            valid_rts = [rt for rt in valid_rts \
                            if rt.properties.extension_hint is not None and \
                               ext in rt.properties.extension_hint.split(',')]

            # check for matching sequence vs. single file
            if hasattr(self._data, "frame_range") and self._data.frame_range is not None:
                resource_type = tank.constants.ResourceType.SEQUENCE
            else:
                if os.path.exists(self._data.path) and os.path.isdir(self._data.path):
                    resource_type = tank.constants.ResourceType.FOLDER
                else:
                    resource_type = tank.constants.ResourceType.SINGLE_FILE

            valid_rts = [rt for rt in valid_rts if rt.properties.restrict_resource_type in (resource_type, None)]

            return [None] + sorted(valid_rts, key=lambda rt: rt.system.name)
        else:
            return [None]

    # property
    def get_container(self):
        """
        Returns the tank container object.

        :rtype: TankContainer or None
        """
        return self._container
    def set_container(self, c):
        assert isinstance(c, tank.TankContainer) or c is None, c
        # check that we're not about to overwrite unflushed changes
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)

        if self._container != c:
            self._container = c
            # invalidate
            self._container_type = None
            self._labels = None
            self._name = None
            self.update()

            # cascade the change to any nodes in the scene with the same path
            #self.scene.set_container_by_path(self.path, self._container)
            for node in self.scene.find_matching_nodes(path=self._data.path, is_revision=False):
                node.container = self._container

    container = property(get_container, set_container)

    # property
    def get_container_type(self):
        """
        Returns the Tank container type object.

        :rtype: TankType or None
        """
        return self._container_type
    def set_container_type(self, ct):
        assert (isinstance(ct, tank.TankType) and ct.properties.container_type == tank.constants.ContainerType.CONTAINER) or ct is None, ct
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if self._container_type != ct:
            self._container_type = ct
            # invalidate
            self._container = None
            self._name = None
            self.update()
    container_type = property(get_container_type, set_container_type)

    @property
    def container_address(self):
        """
        Returns a formatted tank address for the current container.
        """
        if self._container is not None:
            return self._container.system.address
        elif self._labels is not None and self._container_type is not None:
            if self._name is not None:
                return "%s(%s, %s)" % (str(self._container_type.system.name),
                                       str(self._name),
                                       ", ".join(str(l) for l in self._labels.values()))
            else:
                return "%s(%s)" % (str(self._container_type.system.name),
                                   ", ".join(str(l) for l in self._labels.values()))
        else:
            return None

    @property
    def valid_container_types(self):
        """
        Returns a list of valid container types. If this node's revision type is not
        None, only containers whose valid_revision_type property contains the revision
        type are returned. The first entry is always None.

        :rtype: list of EntityType or None
        """
        valid_cts = [tank.find(ct) for ct in tank.list_container_types()]

        if self._revision_type is not None:
            # filter by valid revision type
            valid_cts = [ct for ct in valid_cts if self._revision_type in ct.properties.valid_revision_types or ct.properties.valid_revision_types is None]

        return [None] + sorted(valid_cts, key=lambda ct: ct.system.name)

    # property
    def get_labels(self):
        """
        Returns the list of partial and fully specified labels.

        :rtype: ordered dictionary in the form {label_type: label or None, ...}
        """
        return self._labels
    def set_labels(self, d):
        assert all(isinstance(lt, tank.TankType) and \
                   lt.properties.container_type == tank.constants.ContainerType.LABEL and \
                   (isinstance(l, tank.TankLabel) or l is None) \
                        for lt, l in d.items()), d
        # build an ordered dictionary of label type to label
        assert self._container_type is not None, self._container_type
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)

        # start with a default dictionary
        labels = dict((lt, None) for lt in _get_label_types(self._container_type))
        # add labels
        labels.update(d)

        # assert all are labels
        if self._labels != labels:
            self._labels = dict(labels.items())
            # invalidate
            self._container = None
            self.update()
    labels = property(get_labels, set_labels)

    def valid_labels(self):
        """
        Returns an ordered dictionary of label types to and lists of valid
        labels.

        :rtype: dictionary in the form {label_type: [label1, label2, ...], ...}
        """
        assert self._container_type is not None, self._container_type
        # TODO: switch to using label types as the key and labels as values
        return dict((lt, [None] + tank.get_children(lt)) \
                                for lt in _get_label_types(self._container_type))

    # property
    def get_name(self):
        """
        Returns the container name.

        :rtype: string or None
        """
        return self._name
    def set_name(self, name):
        assert isinstance(name, (str, unicode)) or name is None, "Invalid name: %s (type %s)" % (name, str(type(name)))
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if name == "":
            name = None
        if self._name != name:
            self._name = name
            # invalidate the container
            self._container = None
            self.update()
    name = property(get_name, set_name)

    @property
    def use_name(self):
        """
        Returns the value of the use_name property of the container.

        :rtype: boolean
        """
        return self._container_type is not None and self._container_type.properties.use_name

    def valid_names(self):
        """
        Returns a list of valid names for this container. None is always the first entry.

        :rtype: string or None
        """
        if self._container_type is not None and self._container_type.properties.use_name:
            valid_ns = [c.system.name for c in tank.get_children(self._container_type)]
        else:
            valid_ns = []
        # return sorted and unique list
        return [None] + sorted(set(valid_ns))

    # property
    def get_version(self):
        """
        Returns the revision version.

        :rtype: string or None
        """
        return self._version
    def set_version(self, version):
        if self._pending_action is not None and self._pending_action.name != "update":
            raise UncommittedChangesError(self)
        if self._version != version and self._container is not None and self._revision_type is not None:
            self._version = version
            # invalidate
            self._revision = None
            self.update(reload=True)
    version = property(get_version, set_version)

    @property
    def status(self):
        """
        Returns the status (StatusType)
        """
        if self._version is not None and self._revision_type is not None:
            if len(self._container.properties.recommended) > 0:
                # in the case that we have recommended versions
                if len(self._container.properties.recommended) > 0 and \
                        self._version == sorted([r.system.name for r in self._container.properties.recommended], reverse=True)[0]:
                    return "recommended+latest"
                else:
                    return "recommended+outofdate"
            else:
                # FIXME: not sure why it doesn't work if I omit the string conversion
                # FIXME: fails in tank 1.14, should be fixed in 1.15
                #if str(self._revision) in [str(r) for r in self._container.latest_revisions.values()]:
                if str(self._revision) in [str(r) for r in tank.find(str(self._container)).latest_revisions.values()]:
                    return "general+latest"
                else:
                    return "general+outofdate"
        else:
            return "unknown"

    @property
    def created_at(self):
        if self.is_revision() and self._revision.system.creation_date is not None:
            return tank.common.propertytypes.DateTimePropertyType.utc_to_local_str(self._revision.system.creation_date)
        else:
            return None

    @property
    def created_by(self):
        if self.is_revision():
            return self._revision.properties.created_by.system.name if self._revision.properties.created_by is not None else None
        else:
            #stat_info = os.stat(self._data.path)
            #return pwd.getpwuid(stat_info.st_uid)[0]
            return None

    @property
    def description(self):
        if self.is_revision():
            return self._revision.properties.description
        else:
            return None

#    @property
#    def valid_versions(self):
#        """
#        Returns a list of versions for this container and revision type. The first
#        entry is always None.
#
#        :rtype: list of TankRevisions
#        """
#        if self._container is not None and self._revision_type is not None:
#            valid_rvs = self._container.revisions_dict[self._revision_type.system.name]
#        else:
#            valid_rvs = []
#        return [None] + [r.system.name for r in valid_rvs]
    def find_matching_nodes(self, container=None, revision_type=None, path=None, data=None, is_working=None, is_revision=None):
        """
        Return a list of nodes that match all of the given restrictions. Recurses over dependencies.
        """
        matching_nodes = [node for d in self.dependencies for node in d.find_matching_nodes(container, revision_type, path, data, is_working, is_revision)]

        matches = True
        if container is not None and container != self._container:
            matches = False
        if revision_type is not None and revision_type != self._revision_type:
            matches = False
        if path is not None and path != self._data.path:
            matches = False
        if data is not None and data != self._data:
            matches = False
        if is_working is not None and is_working != self.is_working():
            matches = False
        if is_revision is not None and is_revision != self.is_revision():
            matches = False

        if matches:
            matching_nodes.append(self)

        return matching_nodes

    def matches(self, match_string):
        if match_string in self.node:
            return True

        if self._revision:
            return match_string.lower() in str(self._revision).lower()
        elif self._revision_type:
            return match_string.lower() in str(self._revision_type).lower()
        elif self._container:
            return match_string.lower() in str(self._container).lower()
        else:
            return False

    def _update_revision_properties(self):
        """
        Updates properties that depend on the revision.
        """
        if self._revision_type is None:
            self._revision_type = self._revision.system.type
        if self._version is None:
            self._version = self._revision.system.name
        if self._container is None:
            self._container = self._revision.container
            self._update_container_properties()

        # update our sources
        self._sources = self._revision.properties.sources

    def _update_container_properties(self):
        """
        Updates properties that depend on the container.
        """
        if self._name is None:
            self._name = self._container.system.name
        if self._labels is None:
            # rebuild as a vanilla python dict instead of a tank dict
            self._labels = dict((label.system.type, label) for label in self._container.labels.values())
        if self._container_type is None:
            self._container_type = self._container.system.type
            self._update_container_type_properties()

    def _update_container_type_properties(self):
        """
        Updates properties that depend on the container type.
        """
        if self._labels is None:
            # reset labels
            self._labels = dict((lt, None) for lt in _get_label_types(self._container_type))
        else:
            # remove non-matching labels
            all_label_types = _get_label_types(self._container_type)
            for type in self._labels.keys():
                if type not in all_label_types:
                    del self._labels[type]

#    def _update_children(self, reload):
#        # go through each child revision
#        # find matching dependency with same container
#        # update
#        for child_revision in self._data.children:
#            for d in self.dependencies:
#                if str(d.revision) == str(child_revision):
#                    # perfect match, skip this one
#                    break
#                elif str(d.container) == str(child_revision.container):
#                    # conatiner match!
#                    # update this dependency with the new revision
#                    d.set_revision(child_revision, reload)
#
#        # FIXME: we don't add anything when a bundle has new contents
#
#        # now go through dependencies and remove any that aren't in the list
#        # of children
##        for d in self.dependencies:
##            if not str(d.revision) in (str(child_revision) for child_revision in self._data.children):
##                d.remove()

    def update(self, reload=False):
        """
        Updates properties, creates the container if it does not exist, sets
        the container id and revision type id on the delegate node, and
        schedules a delegate update.
        """
        if hasattr(self._data, "update"):
            self._pending_action = Action("update", self.data.update, kwargs={"reload": reload})

        # fill in any missing properties
        if self._revision is not None:
            self._update_revision_properties()

        if self._container is not None:
            self._update_container_properties()

        if self._container_type is not None:
            self._update_container_type_properties()

        # find or create the container, if possible
        if self._container is None and self._container_type is not None \
                and self._labels is not None \
                and ((self.use_name and self._name is not None) or (not self.use_name and self._name is None)):
            try:
                # attempt to find the container
                self._container = tank.find_ex(self._container_type, name=self._name, labels=self._labels.values())
            except tank.common.errors.TankNotFound:
                # doesn't exist, try to create it
                # TODO: fix this when tank.create_ex is added
                if self._container_type.properties.use_name:
                    address = "%s(%s, %s)" % (self._container_type.system.name, self._name, ', '.join(str(l) for l in self._labels.values()))
                else:
                    address = "%s(%s)" % (self._container_type.system.name, ', '.join(str(l) for l in self._labels.values()))
                self._container = tank.create_container(address)
                self._container.properties.created_by = tank.util.misc.resolve_current_user()
                self._container.save()
                self._update_container_properties()

        # if container type is none, labels must be none
        if self._container_type is None:
            self._labels = None

        # find the revision, if possible
        if self._revision is None and self._container is not None and self._revision_type is not None and self._version is not None:
            self._revision = self._container.find_revision(self._revision_type, self._version)
            self._update_revision_properties()

        # update tank ids on the data, if it is supported
        if hasattr(self._data, "container_id"):
            self._data.container_id = self._container.system.address if self._container is not None else None
        if hasattr(self._data, "revision_type_id"):
            self._data.revision_type_id = self._revision_type.system.address if self._revision_type is not None else None
        if hasattr(self._data, "last_revision_id"):
            self._data.last_revision_id = self._revision.system.address if self._revision is not None else None

        # update the delegate data
        if hasattr(self._data, "update") and self._revision is not None and self._revision.is_published():
            try:
                path = self._revision.system.vfs_full_paths[0]
            except IndexError:
                raise NoVFSRuleError(self._revision)
            if self._revision.resource_type == tank.constants.ResourceType.SINGLE_FILE:
                self._data.path = path
            elif self._revision.resource_type == tank.constants.ResourceType.SEQUENCE:
                self._data.frame_range = self._revision.frame_range
                self._data.path = os.path.join(self._revision.system.vfs_full_paths[0], os.path.split(self._revision.system.filesystem_location)[1])
            else:
                raise OSError("invalid path: ", path)

#        # trigger a child update if the data supports it
#        if hasattr(self._data, "children"):
#            self._update_children(reload)

    @property
    def dependencies(self):
        """
        Returns dependency nodes.

        :rtype: list of Dependency
        """
        return self._dependencies

    @property
    def row(self):
        """
        Returns the relative row in the parent's dependencies list.

        :rtype: integer
        """
        return self.parent.dependencies.index(self)

    @property
    def parent(self):
        """
        Returns the parent node.

        :rtype: Node
        """
        return self._parent

    @property
    def scene(self):
        """
        Returns the root (scene) node.

        :rtype: Scene
        """
        return self.parent.scene

    def get_path(self):
        """
        Returns the delegate's path attribute, the path to the actual file.

        :rtype: string
        """
        if hasattr(self._data, "frame_range") and self._data.frame_range is not None:
            return self._data.path + "," + self._data.frame_range
        else:
            return self._data.path
    def set_path(self, path, reload=False):
        if self._data.path != path:
            self._data.path = path
            self.update(reload)
    path = property(get_path, set_path)

    @property
    def last_revision(self):
        """
        Returns the last revision stored by the delegate
        """
        if self.is_revision():
            return self.revision
        elif hasattr(self._data, "last_revision_id"):
            return tank.find(self._data.last_revision_id) if self._data.last_revision_id is not None else None
        else:
            return None

    def get_publish_mode(self):
        if hasattr(self._data, "frame_range") and self._data.frame_range is not None:
            return tank.constants.PublishMode.MOVE
        elif hasattr(self._data, "save"):
            return tank.constants.PublishMode.DEFERRED
        else:
            return tank.constants.PublishMode.COPY

    def publish(self, description, subset=None, callbacks=None, properties=None):
        """
        Recursively publish this node.

        :param description: The description to use for the publish.
        :type description: string
        :type version: list of strings
        :param callbacks: object with callback attributes:
                              on_progress_change(files_processed, total_files_to_process),
                              on_publish(revision_type, container, filename)
        """

        if self.is_working() and self._container is not None and self.revision_type is not None:
            # recursively publish our dependencies
            published_dependencies = []
            for node in self.dependencies:
                published_dependencies += node.publish(description, subset=subset, callbacks=callbacks)

            if (subset is None or self in subset):
                # save the node before the publish, if not deferred and possible
                if self.get_publish_mode() != tank.constants.PublishMode.DEFERRED and hasattr(self._data, "save"):
                    self._data.save()

                work_path = self._data.path

                # publish our own revision
                revision = self._container.create_revision(revision_type=self._revision_type)
                revision.resource_path = self._data.path
                revision.publish_mode = self.get_publish_mode()

                if hasattr(self._data, "frame_range") and self._data.frame_range is not None:
                    revision.resource_type = tank.common.constants.ResourceType.SEQUENCE
                    revision.frame_range = self._data.frame_range
                else:
                    revision.resource_type = tank.common.constants.ResourceType.SINGLE_FILE

                revision.properties.created_by = tank.find("user=%s" % os.environ["USER"])
                revision.properties.description = description
                revision.properties.dependencies = published_dependencies
                revision.properties.sources = self.sources

                if properties is not None:
                    for k, v in properties.items():
                        revision.properties[k] = v

                # FIXME: Tank API doesn't expose callbacks at the moment
                # tank callbacks
                #for cb in ("on_progress_change", "should_abort", "did_abort", "on_error"):
                #    if hasattr(callbacks, cb):
                #        publisher.add_callback(cb, getattr(callbacks, cb))
                #
                #if hasattr(callbacks, "on_publish"):
                #    callbacks.on_publish(self._revision_type.get_address(),
                #                         self._container.get_address(),
                #                         self._data.path)

                # do it
                revision.save()

                # set our revision to the revision we just published
                self.revision = revision

                # verify that the revision's file(s) are accessible in the vfs
                if hasattr(self._data, "frame_range") and self._data.frame_range is not None:
                    sequence = tank.util.sequence.resolve(self._data.path, self._data.frame_range)
                    if not all(os.path.exists(f) for f in sequence):
                        raise IOError("%s does not exist in the vfs" % self._data.path)
                else:
                    if not os.path.exists(self._data.path):
                        raise IOError("%s does not exist in the vfs" % self._data.path)

                # commit the change. this pushes the change to the path back to the delegate.
                self.commit(recursive=False, callbacks=callbacks)

                # save & seal if this is a deferred publish
                if self.get_publish_mode() == tank.constants.PublishMode.DEFERRED:
                    # save the node if possible
                    # we're now pointing at the new revision, so it should be writable
                    assert hasattr(self._data, "save")
                    self._data.save()
                    revision.seal()

                # update any dependencies that refer to the same path
                self.scene.update_paths(work_path, self._revision, callbacks=callbacks)

                return [self._revision] + published_dependencies
            else:
                return published_dependencies
        else:
            return []

    def update_paths(self, path, revision, callbacks=None):
        """
        Updates dependences that have the given path to the given revision
        """
        for d in self.dependencies:
            d.update_paths(path, revision, callbacks=callbacks)

        if self.is_working() and self.path == path:
            self.revision = revision
            self.commit(recursive=False, callbacks=callbacks)

    def is_revision(self):
        """
        Returns True if this node is a revision, False otherwise.

        :rtype: boolean
        """
        return self._revision is not None

    def is_working(self):
        """
        Returns True if this node is not a revision, False otherwise.

        :rtype: boolean
        """
        return self._revision is None and self._container is not None

    def import_(self):
        raise NotImplementedError

    def save(self):
        """
        Recursively save changes.
        """
        for node in self.dependencies:
            node.save()

        if hasattr(self._data, "save"):
            self.commit()
            self._data.save()

    def commit(self, recursive=True, callbacks=None):
        """
        Recursively commit changes back to the delegate.
        :param callbacks: object with callback attributes:
                              on_progress_change(files_processed, total_files_to_process),
                              on_publish(revision_type, container, filename)
                              on_execute(action, revision_type, container, filename)
        """
        if recursive:
            # commit our dependencies
            for node in self.dependencies:
                node.commit(callbacks=callbacks)

        # commit ourself
        if self._pending_action is not None:
            self._pending_action.execute()
            if hasattr(callbacks, "on_execute"):
                callbacks.on_execute(self._pending_action.name, str(self._revision_type), str(self._container), self.path)
            self._pending_action = None

    def validate(self):
        """
        Perform checks that this node (and optionally, children):
         * have a legal combination of revision type and container type
         * have all required labels filled in
         * container/revision_type has a single path
        :param recursive: If True, also check dependencies
        :type recursive: bool
        :raises: InvalidNodeError
        """
        # check that the revision type is allowed for this container type
        if self.revision_type is None:
            raise InvalidNodeError(self.node, "Revision type is unspecified.")
        elif self.container is None:
            raise InvalidNodeError(self.node, "Container is unspecified.")
        elif self.container_type is None:
            raise InvalidNodeError(self.node, "Container type is unspecified.")
        elif self.use_name is True and self.name is None:
            raise InvalidNodeError(self.node, "The %s container requires a name, but none is specified." % self.container.get_address())
        elif self.revision_type is None:
            raise InvalidNodeError(self.node, "Revision type is unspecified.")
        elif None in self.labels.values():
            raise InvalidNodeError(self.node, "One or more labels are unspecified.")
        elif self.revision_type not in self.valid_revision_types:
            raise InvalidNodeError(self.node, "%s is not a valid revision type." % self.revision_type.system.address)

        if self.is_working():
            # check that this container/revision_type combo isn't already in use
            matching_container_nodes = set(self.scene.find_matching_nodes(container=self._container, revision_type=self._revision_type, is_revision=False))
            matching_path_nodes = set(self.scene.find_matching_nodes(path=self._data.path, is_revision=False))

            # containers may only be reused by working nodes if they share the same path
            if not matching_container_nodes.issubset(matching_path_nodes):
                raise NonUniqueWorkingContainerError(matching_container_nodes, self._container)

            for child in self.dependencies:
                child.validate()

    def is_dirty(self):
        """
        Returns True if an action is pending, False otherwise.

        :rtype: boolean
        """
        return self._pending_action is not None

    def is_removed(self):
        """
        Returns True if a remove action is pending, False otherwise.

        :rtype: boolean
        """
        return self._pending_action.name == "remove" if self._pending_action is not None else False

    @property
    def actions(self):
        """
        Returns a list of valid actions for this node.

        :rtype: ordered dictionary in the form [{"action": Action}, ...]
        """
        if self._actions is None:
            self._actions = {}

            for p in plugins.get_actions():
                # each call to get_actions adds more
                try:
                    self._actions = p.get_actions(self, self._actions)
                except Exception, e:
                    print "Skipping %s: %s" % (p.__name__, e)
                    import traceback
                    traceback.print_exc()
                    # don't let bad plugins bring me down
                    pass

        return self._actions

    @property
    def action_names(self):
        names = dict((id, action.name) for id, action in self.actions.items())
        for node in self.dependencies:
            names.update(node.action_names)
        return names

    def __repr__(self):
        if self.revision is not None:
            return "<%s: %s, Rev: %s>" % (type(self), self.node, self.revision)
        else:
            return "<%s: %s, Container: %s, Rev Type: %s>" % (type(self), self.node, self.container, self.revision_type)

    @property
    def depth(self):
        if self._parent is None:
            return 1
        else:
            return self._parent.depth + 1

    def add_dependency(self, path, subset=(), name=None, delegate=None):
        """
        Explicitly adds a dependency to the scene.
        :param path: The path to the dependency. Dependencies are resolved using
                     delegates in Node.__init__.
        :type path: string
        :param subset: subset of child revisions that will be added. this must be
                       a subset of new_dependency.data.children
        """
        try:
            revision = None
            container, revision_type = sandbox.get(path)
            ext = os.path.splitext(path)[1]
            frame_range = None
        except:
            revision = tank.find(path)
            container = revision.container
            revision_type = revision.system.type
            ext = os.path.splitext(revision.resource_path)[1]
            if revision.resource_type == tank.constants.ResourceType.SEQUENCE:
                frame_range = revision.frame_range
                path = os.path.join(revision.system.vfs_full_paths[0], os.path.split(revision.resource_path)[1])
            else:
                frame_range = None

        # find matching delegate
        if delegate is None:
            delegate = plugins.get_one_delegate(ext=ext, attrs=("add_dependency",))

        # consult the namer plugin
        if name is None:
            name = plugins.get_one_namer().get_node_name(self.container, container, revision_type, path)

        data = delegate.add_dependency(name, path, frame_range, self._data)
        dependency = Dependency(delegate, data, self)

#        # add any children first
#        for r in data.children:
#            if r in subset:
#                dependency.add_dependency(r.system.vfs_full_paths[0])

        self.dependencies.append(dependency)
        if hasattr(data, "update"):
            #children = [d.data for d in dependency.dependencies]
            dependency._pending_action = Action("update", func=data.update, kwargs={"reload": True})

        return dependency


class Dependency(Node):
    """
    Specialized node that represents a dependency.
    """
    def import_(self):
        """
        Schedules the delegate for import.
        """
        assert hasattr(self._data, "import_"), self._data
        self._pending_action = Action("import", func=self._data.import_)

    def remove(self):
        """
        Schedules the delegate for removal.
        """
        if hasattr(self._data, "remove"):
            self._pending_action = Action("remove", func=self._data.remove)


class Scene(Node):
    """
    Specialized node that represents a scene. Scenes can contain
    dependencies and revisions.
    """
    def __init__(self, delegate, path=None):
        """
        Initializes the scene with the given delegate and path.

        :param delegate: Delegate to use for the scene
        :type delegate: Delegate
        :param path: Path to use for the scene, if applicable
        :type path:  string
        """
        if path is None:
            data = delegate.get_scene()
        else:
            data = delegate.get_scene(path)

        super(Scene, self).__init__(delegate, data)

    @property
    def row(self):
        return 0

    @property
    def scene(self):
        return self

    def get_publish_mode(self):
        # publish scene as deferred so that the updated tkids on nodes (and the scene itself) are saved
        return tank.constants.PublishMode.DEFERRED

    def publish(self, description, subset=None, callbacks=None, properties=None):
        try:
            self.validate()
        except InvalidNodeError, e:
            import traceback
            traceback.print_exc()
            print "Warning: " + str(e)

        return super(Scene, self).publish(description, subset=subset, callbacks=callbacks, properties=properties)

    # override set_revision to not reload the scene by default
    def set_revision(self, r, reload=None):
        if reload is None:
            reload = False
        super(Scene, self).set_revision(r, reload)
    revision = property(Node.get_revision, set_revision)
