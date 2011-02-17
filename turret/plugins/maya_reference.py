from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, ref=None):
        assert ref is None or ref.isUsingNamespaces()
        self.reference = ref
        super(Data, self).__init__(type="MayaReference",
                                   name=name,
                                   path=path,
                                   node=ref.refNode if ref is not None else None)
        # child nodes are those in our namespace
        self.child_nodes = pm.ls(ref.namespace + ":*") if ref is not None else []

    def _readName(self):
        if self.reference is not None:
            self.name = self.reference.namespace

    def _readPath(self):
        if self.reference is not None:
            self.path = str(self.reference.path)

    def _writeName(self):
        if self.reference is not None:
            if self.name != self.reference.namespace:
                # rename the namespace
                self.reference.namespace = self.name
                # also try to rename the reference node (which isn't renamed above)
                try:
                    self.reference.refNode.unlock()
                    self.reference.refNode.rename(self.name + "RN")
                except:
                    pass
                finally:
                    self.reference.refNode.lock()

    def _writePath(self, reload):
        if self.reference is not None:
            if self.path != self.reference.path and reload:
                self.reference.replaceWith(self.path)

    def _createNode(self):
        assert self.reference is None
        self.reference = pm.createReference(self.path, namespace=self.name)
        # Maya automatically increments the namespace in case of conflict
        self.name = self.reference.namespace
        return self.reference.refNode

    def _deleteNode(self):
        if self.reference is not None:
            self.reference.remove()
            self.reference = None

    def import_(self):
        if self.reference is not None:
            self.reference.importContents(removeNamespace=True)
            self.reference = None
            self.node = None

    def remove(self):
        if self.reference is not None:
            self.reference.remove()
            self.reference = None

    def select(self):
        self.reference.selectAll()


def supports_ext(ext):
    return ext in (".ma", ".mb")

def get_dependencies(parent):
    # TODO: note that a double reference is not currently re-exported, so the nested
    #       reference will not be updated to point at the published file
    refs = pm.getReferences(parentReference=parent.reference if hasattr(parent, "reference") else None,
                            recursive=False)
    # only support references with namespaces
    return [Data(ref=ref) for ref in refs.values() if ref.isUsingNamespaces() and ref.refNode in parent.child_nodes]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)

