import webob
import json
import socket
import select
import threading
import logging

class XigConsoleHandler(threading.Thread):
    def __init__(self, port = None):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self,True)
        self.port = port
        self.udp_sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.received_data = ""
        self.lock = threading.RLock() #used for self.received_data
        self.logger = logging.getLogger('xig.gui')
    
    def run(self):
        while 1:
            while self.port and select.select([self.udp_sd], [], [], 5)[0]:
                buf = self.udp_sd.recv(4096)
                self.lock.acquire()
                self.received_data += buf
                self.lock.release()
    
    def send(self, data):
        if not self.port:
            raise Exception("No UDP target.")
        self.udp_sd.sendto(data, 0, ('localhost', self.port))

    def poll(self, refresh=False): #NOTE: refresh not used.
        if self.received_data:
            self.lock.acquire()
            response = self.received_data
            self.received_data = ""
            self.lock.release()
            return response
        return None
    
    def __call__(self, request):
        if request.method == 'GET':
            response = self.poll() or ""
            return webob.Response(json.dumps(response), content_type='json')
        elif request.method == 'POST':
            data = request.POST.get('data')
            self.send(data)
            return webob.Response()
        else:
            return webob.exc.HTTPMethodNotAllowed()
    
    def __del__(self):
        if self.udp_sd:
            self.udp_sd.close()
