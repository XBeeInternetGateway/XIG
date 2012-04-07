import os
import mimetypes
import webob

class StaticHandler:
    
    def __init__(self):
        self.static_folder = os.path.join(os.path.dirname(__file__), '..', 'static')
        if not os.path.exists(self.static_folder):
                self.static_folder = os.path.join(os.path.curdir, 'static')        
        if not os.path.exists(self.static_folder):
                self.static_folder = os.path.join(os.path.curdir, 'gui', 'static')        
        
    def __call__(self, request):
        if request.method == 'GET':
            # normalize path
            path = os.path.normpath(os.path.join(*(request.path.split('/'))))
            path = path.replace('\\', '/') # in case the slashes get reversed
            if path.startswith('/'):
                path = path[1:] #remove leading '/' for processing
            # special case the favicon.ico
            if path == 'favicon.ico':
                path = 's/favicon.ico'
            # create list from path
            path_list = list(path.split('/'))
            if path_list[0] not in ['s', 'static']:
                # uh oh, outside of static folder
                return webob.exc.HTTPForbidden()
            #TODO: do this in a nice generic way.
            if len(path_list) > 1:
                # let's check to see if we need to shortcut the css or js paths
                if path_list[1] == 'js':
                    path_list[1] = 'js_uncompressed'
                if path_list[1] == 'css':
                    path_list[1] = 'css_uncompressed'
            # create the absolute file name
            filename = os.path.join(self.static_folder, *(path_list[1:]))
            if os.path.isfile(filename):
                # OK, we've got the file, let's get the mimetype and return the file. 
                content_type = mimetypes.guess_type(filename)[0] # ignoring encoding for now
                content_type = content_type or 'application/octet-stream'
                response = webob.Response(content_type=content_type)
                try:
                    file = open(filename, 'rb') 
                    response.body = file.read()
                finally:
                    file.close()
                return response
        else:
            # unhandled request type
            return webob.exc.HTTPMethodNotAllowed()
