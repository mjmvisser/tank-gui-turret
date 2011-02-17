import os, re
import tank

def get_node_name(parent_container, container, revision_type, path):
    # attempt to come up with a useful node name
    name = None

    # 1. if all of the new container's labels are contained in our container's labels,
    #    use the new container type's name (sans _vXX)
    # example: referencing a model in a texture should call the namespace "model"
    if parent_container is not None and container is not None \
            and all(l in container.labels.values() for l in parent_container.labels.values()):
        name = re.sub(r"_v[0-9]+", "", container.system.type_name)

        # 1a. if the container has a name, append that with an underscore, e.g. "model_arm"
        if tank.find(container.system.type_name).properties.use_name:
            name += "_" + container.system.name

    # 2. if the container has an Asset label that is not ANY, use that with 01 appended
    elif container.labels.has_key("Asset") and container.labels["Asset"].system.name != "ANY":
        name = container.labels["Asset"].system.name + "01"

    # 3. if the container has a name, use that with 01 appended
    elif container is not None and container.system.type.properties.use_name:
        name = container.system.name + "01"

    # 4. use the first label's value that doesn't start with a number, with 01 appended
    elif container is not None and len(container.labels.values()) > 0:
        for label in container.labels.values():
            if label.system.name[0].isalpha():
                name = label.system.name
                break
        if name is not None:
            name += "01"

    # 5. fall back on using the filename minus extensions
    if name is None:
        name = os.path.split(path)[1]
        while name.find('.') != -1:
            name = os.path.splitext(name)[0]

    # camelCaps, not CapitalCaps
    name = name[0].lower() + name[1:]

    return name

def get_container(parent_container, container, revision_type, path):
    if container is not None:
        template_container = container
    elif parent_container is not None:
        template_container = parent_container
    else:
        return None

    labels = get_labels(parent_container, container, revision_type, path)

    name = get_name(parent_container, template_container.system.name, labels, revision_type, path)

    candidates = tank.get_children(template_container.system.type, ["labels contains %s" % l for l in labels.values()]).fetch_all()

    for c in candidates:
        if c.system.name == name:
            return c

    for c in candidates:
        if c.system.name == template_container.system.name:
            return c

    return None

def get_revision_type(parent_container, path, frame_range):
    # start with all revision types
    valid_rts = [tank.find(rt) for rt in tank.list_revision_types()]

    if parent_container and len(parent_container.system.type.properties.valid_revision_types) > 0:
        valid_rts = [rt for rt in valid_rts if rt in parent_container.system.type.properties.valid_revision_types]

    # filter by extension
    ext = os.path.splitext(path)[1].lstrip(".")
    valid_rts = [rt for rt in valid_rts \
                    if rt.properties.extension_hint is not None and \
                       ext in rt.properties.extension_hint.split(',')]

    # filter by resource type
    if frame_range is None:
        if os.path.exists(path) and os.path.isdir(path):
            resource_type = tank.common.constants.ResourceType.FOLDER
        else:
            resource_type = tank.common.constants.ResourceType.SINGLE_FILE
    else:
        resource_type = tank.common.constants.ResourceType.SEQUENCE

    valid_rts = [rt for rt in valid_rts if rt.properties.restrict_resource_type in (resource_type, None)]

    if len(valid_rts) > 0:
        return valid_rts[0]
    else:
        return None

def get_labels(parent_container, container, revision_type, path):
    # passthrough if container is not the same as our parent
    if container is not None and parent_container != container:
        return dict((l.system.type, l) for l in container.labels.values())

    else:
        # try to specify the optional label(s) using the path
        if container is not None:
            template_container = container
        else:
            template_container = parent_container

        if "ANY" in (l.system.name for l in template_container.labels.values()):
            template_labels = dict((l.system.type, l) for l in template_container.labels.values())
            target_labels = dict((l.system.type, l) for l in template_container.labels.values())
            filename = os.path.splitext(os.path.split(path)[1])[0]

            # override optional labels if there is a match in the path
            for label_type, label in template_labels.items():
                if label.system.name == "ANY":
                    for potential_label in tank.get_children(label_type).fetch_all():
                        if potential_label.system.name in filename:
                            target_labels[label_type] = potential_label
                            break

            return target_labels

        # no idea, default to the parent
        else:
            return dict((l.system.type, l) for l in parent_container.labels.values())

def get_name(parent_container, name, labels, revision_type, path):
    # if we have a parent container, use the filename
    if parent_container is not None:
        filename = os.path.splitext(os.path.split(path)[1])[0]

        # remove _labelName from the filename, if it exists
        for l in labels.values():
            filename = re.sub(r"_?%s_?" % l.system.name, "", filename)

        return filename
    else:
        return name
