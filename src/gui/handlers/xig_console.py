import webob
import json
import socket
import select

class XigConsoleHandler:
    def __init__(self, port = None):
        self.port = port
        self.udp_sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send(self, data):
        if not self.port:
            raise Exception("No UDP target.")
        #TODO: use a select here?
        self.udp_sd.sendto(data, 0, ('localhost', self.port))

    def poll(self):
        response = ""
        while self.port and select.select([self.udp_sd], [], [], 0)[0]:
            response += self.udp_sd.recv(1024)
        return response or None
    
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
