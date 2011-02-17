import os
import tank
from turret.tankscene import Action, Param, ActionError
from turret.plugins import UnsupportedPluginError
import plugin_utils
try:
    import pymel.core as pm
except ImportError:
    raise UnsupportedPluginError()

class haircacheError(Exception):
    pass

def get_actions(node, actions):
    """Returns a dictionary of actions supported by node."""
    if node.delegate.__name__ == "maya_reference":
        # TODO: check that the node has a hair system
        actions["attach_haircache"] = Action("Attach Hair Caches",
                                             func=attach_haircaches, args=[node])

    return actions

def attach_haircaches(node):
    namespace = node.data.reference.namespace
    start_time = pm.playbackOptions(query=True, minTime=True)
    end_time = pm.playbackOptions(query=True, maxTime=True)
    node_labels = node.labels.values()
    scene_labels = node.scene.labels.values()
    container_type = tank.find(plugin_utils.get_latest_container('Anim_v'))

    # find hairsystems in the given namespace
    for hairsystem in pm.ls(namespace + ":*", type="hairSystem"):
        name = str(hairsystem.stripNamespace())

        # find container with node and scene labels named the same as the
        # hair system (same type as scene container)
        labels_set = set(node_labels + [label for label in scene_labels if label.system.type.system.name != 'Layer'])
        container = tank.find_ex(container_type, name=name, labels=labels_set)


        # find latest revision of type HairCache
        revision = container.latest_revisions["HairCache"]
        cache_filename = revision.system.vfs_full_paths[0]

        cache_name = "cache_" + namespace.replace(":", "_") + "_" + name

        if pm.objExists(cache_name):
            diskcache = pm.ls(cache_name)
        else:
            # create and set-up the node
            diskcache = pm.createNode("diskCache", name=cache_name)

        hairsystem_start_time = hairsystem.startFrame.get()

        # set the start/end time
        diskcache.startTime.set(hairsystem_start_time)
        diskcache.endTime.set(end_time)

        # set some sane defaults
        diskcache.enable.set(True)
        diskcache.samplingType.set(0)
        # TODO: may need to grab this from a revision attribute
        diskcache.samplingRate.set(1)
        diskcache.cacheType.set("mchp")
        diskcache.copyLocally.set(1)

        # set the filename
        if diskcache.cacheName.isLocked():
            diskcache.cacheName.unlock()
        diskcache.cacheName.set(cache_filename)
        # need to lock it to prevent it from being changed on save
        diskcache.cacheName.lock()

        # not sure what this is for, but the cache is ignored if it's not set
        # following the naming convention maya uses: hidden1_namespace_hairSystemName.mchp
        if diskcache.hiddenCacheName.isLocked():
            diskcache.hiddenCacheName.unlock()
        hidden_cache_name = "hidden1_" + namespace.replace(":", "_") + "_" + name + ".mchp"
        diskcache.hiddenCacheName.set(hidden_cache_name)

        # finally, connect the cache node to the hair system
        if not diskcache.diskCache.isConnected():
            diskcache.diskCache.connect(hairsystem.diskCache)
