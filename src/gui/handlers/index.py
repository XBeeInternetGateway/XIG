import os
import webob

class IndexHandler:
    
    def __call__(self, request):
        if request.method == 'GET':
            # return the main page
            filename = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
            if not os.path.exists(filename):
                filename = os.path.join(os.path.curdir, 'templates', 'index.html')
            if not os.path.exists(filename):
                filename = os.path.join(os.path.curdir, 'gui', 'templates', 'index.html')
            fp = open(filename) 
            try:
                return webob.Response(fp.read(), content_type='text/html')
            finally:
                fp.close()
        else:
            return wwebob.exc.HTTPMethodNotAllowed()

