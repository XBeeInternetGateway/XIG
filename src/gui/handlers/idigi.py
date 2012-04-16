import webob
import json
import rci

class idigiHandler:

    def __init__(self):
        self.connected = None
        
    def poll(self, refresh=False):
        if refresh or self.connected != rci.connected():
            return self.get_connected_string()
        return None
                
    def get_connected_string(self):
        connected = rci.connected()
        self.connected = connected
        if connected:
            return "Connected"
        else:
            return "Connecting..."

    def __call__(self, request):
        if request.method == 'GET':
            if rci.connected():
                response = "Connected"
            else:
                response = "Connecting..."
            return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()
