import webob
import json
import rci

class idigiHandler:

    def __call__(self, request):
        if request.method == 'GET':
            if rci.connected():
                response = "Connected"
            else:
                response = "Connecting..."
            return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()
