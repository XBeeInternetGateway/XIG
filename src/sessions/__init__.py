"""
XIG Services Library
"""
__version__ = '1.3.0'
__author__ = 'Jordan Husney'
__license__ = 'LGPL'

import sys

from abstract import AbstractSession
from abstract_autostart import AbstractAutostartSession
from library.classloader import classloader
# XigSession is required and is always imported:
from xig import XigSession


# HACK: this causes the ESP project builder to always
# include the sessions sub-modules in the project release:
if sys.platform is None:
    # Add to this import list if you create more sessions:
    import http
    import idigi_data
    import idigi_rci
    import io_sample
    import udp
    import osc

# Add to this map if you create more sessions: 
SESSION_MODEL_CLASS_MAP = {
    "http": ["HTTPSession"],
    "idigi_data": [ "iDigiDataAutostartSession", "iDigiDataSession" ],
    "idigi_rci": ["iDigiRCIAutostartSession", "iDigiRCISession"],
    "io_sample": ["ioSampleSessionAutostartSession"],
    "udp": ["UDPSession"],
    "osc": ["OSCSession"],
}
