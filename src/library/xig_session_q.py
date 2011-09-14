'''
Created on Sep 4, 2011

@author: jordanh

The XigSessionQ class definition.

A XigSessionQ object is used by the XigIOKernel in order to control
and queue multiple destinations waiting on the same XBee resource.

'''


class XigSessionQ(object):
    def __init__(self, xig_core):
        self.__session_q = {}
        self.__global_max_dest_session_q_len = (
            xig_core.getConfig().global_max_dest_session_q_len)
        
    def add(self, session):
        """\
            Add a session to the session queue.
            
            Will raise OverflowError if the session queue is full for
            a given destination.
        """
        key = session.getXBeeAddr()
        if session not in self.__session_q:
            self.__session_q[key] = []
        if (len(self.__session_q[key]) >= 
            self.__global_max_dest_session_q_len):
            raise exceptions.OverflowError, "session queue full"
        self.__session_q[key].append(session)
        
    def waiting_destinations(self):
        """\
            Returns a list of destinations waiting to processing by the IO
            Loop.
        """
        return self.__session_q.keys()
    
    def dequeue_session(self, destination):
        """\
            Returns a waiting session based on a destination.
        """
        session = self.__session_q[destination].pop(0)
        if not len(self.__session_q[destination]):
            del(self.__session_q[destination])
        return session
