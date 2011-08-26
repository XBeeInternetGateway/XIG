"""
A dynamic class loader.

Returns any object from a desired module, including within nested modules.

Based on concepts from v1.3 of
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/223972
by Robert Brewer.

"""

import sys, types

class ClassloaderObjectNotFound(Exception):
    """Exception raised when we fail to load the requested object"""
    pass

def classloader(module_name, object_name):
    """
    Retrieve `object_name` from `module_name`, importing the module if
    necessary.

    Allows for more run-time control of the objects that are brought
    into the running system. Primarily used in the
    :class:`~common.abstract_service_manager.AbstractServiceManager`
    objects to pull in objects that they own specified by the
    settings.
    
    """
    # Get a reference to a given module...
    a_module = None
    if module_name in sys.modules:
        # ...from one that has been loaded:
        a_module = sys.modules[module_name]
    else:
        # ...by loading it dynamically:
        a_module = __import__(module_name, globals(), locals(), [''])

    obj = a_module.__dict__.get(object_name)
    if obj is None:
        raise ClassloaderObjectNotFound, \
            "cannot find '%s' in module '%s'" % (object_name, module_name)

    return obj

