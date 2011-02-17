import os, imp

class UnsupportedPluginError(Exception):
    pass

class NoMatchingPluginError(Exception):
    pass

# singleton list of plugins
_plugins = []

#
# read plugins from TURRET_PLUGIN_PATH
#

def _add_plugin_dir(path):
    """
    Adds plugins from dir to _delegates.
    """
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            item_name, item_ext = os.path.splitext(item)
            if item_ext == ".py":
                try:
                    m = imp.load_source(item_name, os.path.join(path, item))
                    # save the name in the metadata
                    m.__name__ = item_name
                except UnsupportedPluginError:
                    # silently skip this plugin
                    pass
                else:
                    _plugins.append(m)

def initialize():
    global _plugins
    _plugins = []
    for dir in os.environ["TURRET_PLUGIN_PATH"].split(':'):
        if len(dir) > 0:
            _add_plugin_dir(dir)

def get_delegates(name=None, ext=None, attrs=None):
    """
    Returns the list of all delegates matching the given conditions

    :rtype: list of delegates
    """
    global _plugins
    delegates = [p for p in _plugins if hasattr(p, "supports_ext")]
    if name is not None:
        delegates = [d for d in delegates if d.__name__ == name]
    if ext is not None:
        delegates = [d for d in delegates if d.supports_ext(ext)]
    if attrs is not None:
        delegates = [d for d in delegates if all(hasattr(d, a) for a in attrs)]

    return delegates

def get_one_delegate(name=None, ext=None, attrs=None):
    try:
        return get_delegates(name, ext, attrs)[-1]
    except IndexError:
        raise NoMatchingPluginError("No matching plugin for name=%s, ext=%s, attrs=%s" % (str(name), str(ext), str(attrs)))

def get_actions(name=None):
    """
    Returns the list of all actions matching the given conditions

    :rtype: list of delegates
    """
    global _plugins
    actions = [p for p in _plugins if hasattr(p, "get_actions")]
    if name is not None:
        actions = [a for a in actions if a.__name__ == name]
    return actions

def get_one_action(name=None):
    try:
        return get_actions(name)[-1]
    except IndexError:
        raise NoMatchingPluginError("No matching plugin for name=%s" % str(name))

def get_namers(name=None):
    """
    Returns the list of all actions matching the given conditions

    :rtype: list of delegates
    """
    global _plugins
    namers = [p for p in _plugins if hasattr(p, "get_name")]
    if name is not None:
        namers = [n for n in namers if n.__name__ == name]
    return namers

def get_one_namer(name=None):
    try:
        return get_namers(name)[-1]
    except IndexError:
        raise NoMatchingPluginError("No matching plugin for name=%s" % str(name))
