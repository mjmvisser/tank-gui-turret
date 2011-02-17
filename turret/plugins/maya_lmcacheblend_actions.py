import os
import tank
from turret.tankscene import Action, Param, ActionError
from turret.plugins import UnsupportedPluginError
import plugin_utils

try:
    import pymel.core as pm
except ImportError:
    raise UnsupportedPluginError()

class GeocacheError(ActionError):
    pass

def get_actions(node, actions):
    """Returns a dictionary of actions supported by node."""
    if node.delegate.__name__ == "maya_reference":
        actions["attach_geocache"] = Action("Attach Geocache...",
                                            func=attach_geocache, args=[node],
                                            params=[Param("geocache", Param.Revision)])
    elif node.delegate.__name__ == "maya_scene":
        actions["load_all_geocaches"] = Action("Load all geocaches (and texture assets)",
                                               func=load_all_geocaches, args=[node])
        actions["load_one_geocache"] = Action("Load one geocache (and texture asset)",
                                              func=load_one_geocache, args=[node],
                                              params=[Param("geocache", Param.Revision)])
    return actions

def _attach_geocache_to_asset(asset_namespace, geocache):
    """Attaches the given geocache asset to the given namespace"""
    cache_name = asset_namespace + "_cacheDefBlend"
    print "\nAttaching %s to %s...\n" % (cache_name, asset_namespace)

    # Get path (of the first frame)
    cache_path = os.path.join(geocache.system.vfs_full_paths[0],
                              os.path.split(geocache.system.sequence_files[0])[1])
    # Check the extension
    if os.path.splitext(cache_path)[1] != ".mcd":
        raise GeocacheError("%s is not a valid geocache" % cache_path)

    # Get the frame range
    start = geocache.asset.labels.Shot.properties.frame_start
    end = geocache.asset.labels.Shot.properties.frame_end

    # Select all shapes in our namespace
    try:
        pm.select(asset_namespace + ":*:geo", replace=True, hierarchy=True)
    except:
        try:
            pm.select(asset_namespace + ":geo", replace=True, hierarchy=True)
        except:
            raise GeocacheError("No geo node found, can't attache cache")

    shapes = pm.ls(geometry=True, selection=True)
    pm.select(shapes)

    cachedef_nodes = pm.mel.lm_cacheDefBlendApply(0)

    # Rename nodes to something useful
    cachedef_nodes = [node.rename(cache_name + str(i)) for i, node in enumerate(pm.ls(cachedef_nodes))]

    for node in cachedef_nodes:
        node.cacheList[0].fileName.set(cache_path)
        node.cacheList[0].label.set(cache_name)
        node.cacheList[0].enabled.set(1)
        node.cacheList[0].dataSpace.set(1) # Object=0, World=1
        node.cacheList[0].deformSpace.set(1)
        node.cacheList[0].indexMode.set(1)
        node.cacheList[0].globalWeight.set(1)
        node.cacheList[0].startIndex.set(start)
        node.cacheList[0].endIndex.set(end)


def attach_geocache(node, geocache):
    print "attach_geocache(%s, %s)" % (node, geocache)
    _attach_geocache_to_asset(node.data.reference.namespace, geocache)


def load_one_geocache(node, cache):
    print "\nload_one_geocache(%s, %s)" % (node, cache)

    # Get latest texture asset
    asset_container = tank.find_ex(plugin_utils.get_latest_container('Texture_v'),
                                   name='texture',
                                   labels=[cache.container.labels.Asset, cache.container.labels.AssetType])

    texture_latest_rev  = asset_container.latest_revisions['MayaScene']

    # Load texture
    print "\nLoading texture %s...\n" % texture_latest_rev
    texture_ref = node.scene.add_dependency(texture_latest_rev.system.vfs_full_paths[0])
    node.commit()

    # Attach the cache to the texture
    attach_geocache(texture_ref, cache)


def load_all_geocaches(node):
    # Get the shot from the scene container
    shot = node.scene.container.labels['Shot']

    print "\nLoading all geocaches for", shot

    # get all latest geocaches for that shot
    geocaches = tank.get_children(tank.find("GeoCache"), ["container has_label %s" % shot])
    for geocache in geocaches:
#        if geocache == geocache.container.latest_revisions['GeoCache']:  # is it the latest?
        if geocache == tank.find('GeoCache(LATEST, %s)' % geocache.container):  # is it the latest?
            # We only load the latest geocaches revisions
            load_one_geocache(node, geocache)
