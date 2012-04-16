import webob
import json
import logging
import time

logs = []
class CustomHandler(logging.Handler):
    
    def handle(self, record):
        global logs
        logs.append(record)

custom_handler = CustomHandler()
logger = logging.getLogger('')
logger.addHandler(custom_handler)

class LogsHandler:
    def poll(self, refresh=False): #NOTE: refresh not used
        global logs
        response = []
        # copy logs in thread-safe way
        while logs:
            record = logs.pop(0)
            if not hasattr(record, 'asctime'):
                record.asctime = time.ctime(record.created)
            response.append(record.__dict__)
        if not response:
            return None
        return response
    
    def __call__(self, request):
        if request.method == 'GET':
            response = self.poll() or []
            return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()
