import os
import webob

class IndexHandler:
    
    def __call__(self, request):
        if request.method == 'GET':
            # return the main page
            file = open(os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html'))
            try:
                return webob.Response(file.read(), content_type='text/html')
            finally:
                file.close()
        else:
            return wwebob.exc.HTTPMethodNotAllowed()

