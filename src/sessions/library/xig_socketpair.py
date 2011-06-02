'''
Created on Sep 18, 2010

@author: jordanh
'''

"""
"""

import threading
import time
import sys
from socket import *

class SocketPairEmulation(threading.Thread):
    def __init__(self):
        # We go through this rigamarole because Windows does not natively
        # support socketpair():
        listen_sd = socket(AF_INET, SOCK_STREAM)
        listen_sd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listen_sd.bind( ('localhost', 0) )
        listen_iface, self.__listen_port = listen_sd.getsockname()
        listen_sd.listen(1)
        
        self.remote_sd = socket(AF_INET, SOCK_STREAM)
        self.local_sd = None
        
        threading.Thread.__init__(self, name="SocketPairEmulation")
        threading.Thread.setDaemon(self, 1)
        threading.Thread.start(self)
        # execution continues asynchronously at run() method
        self.local_sd, local_addr = listen_sd.accept()
        # sockets are connected to one another at this point
        listen_sd.close()

    def socketpair(self):
        return self.remote_sd, self.local_sd

    def run(self):
        # Complete the socket handshake:
        try:
            self.remote_sd.connect( ('localhost', self.__listen_port) )
        except:
            self.remote_sd, self.local_sd = None, None


def socketpair():
    if sys.platform.lower().startswith("win"):
        SPE = SocketPairEmulation()
        return SPE.socketpair()
    
    return socketpair()

        