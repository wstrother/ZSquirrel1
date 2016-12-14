from importlib import import_module


def get_environment(name):
    cls_name = [word.capitalize() for word in name.split("_")]
    cls_name = "".join(cls_name)

    i_name = "zs_utils." + name
    module = import_module(i_name)

    return getattr(module, cls_name)
