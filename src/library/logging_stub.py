"""Simulate some of the functions of the logging module"""

import sys

try:
    import logging #@UnusedImport
except:
    # logging module does not exist on this platform, insert this module instead
    sys.modules['logging'] = sys.modules[__name__]

DEBUG = 0
INFO = 1
WARN = 2
WARNING = 2
ERROR = 3
CRITICAL = 4

class LoggerStub:
    loggers = {}
    
    def __init__(self, name):
        self.name = name
        self.level = DEBUG
        self.loggers[name] = self
    
    def debug(self, msg, *args):
        self.log("DEBUG", msg, *args)

    def info(self, msg, *args):
        self.log("INFO", msg, *args)

    def warn(self, msg, *args):
        self.log("WARN", msg, *args)

    def warning(self, msg, *args):
        self.log("WARN", msg, *args)

    def error(self, msg, *args):
        self.log("ERROR", msg, *args)

    def critical(self, msg, *args):
        self.log("CRITICAL", msg, *args)

    def log(self, level, msg, *args):
        if self.name:            
            msg2 = "%s:%s" % (level, msg)
        else:
            msg2 = "%s:%s:%s" % (level, self.name, msg)            
        print msg2 % args

    def setLevel(self, level):
        self.level = level

class StreamHandler(object):
    def __init__(*args):
        pass

    def setFormatter(*args):
        pass

class Formatter(object):
    def __init__(*args):
        pass

def getLogger(name=None):
    return LoggerStub.loggers.get(name, LoggerStub(name))

def debug(msg):
    getLogger().debug(msg)

def info(msg):
    getLogger().info(msg)
    
def warn(msg):
    getLogger().warn(msg)
    
def warning(msg):
    getLogger().warn(msg)
    
def error(msg):
    getLogger().error(msg)

def critical(msg):
    getLogger().critical(msg)

def basicConfig():
    pass

