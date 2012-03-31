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
for log_name in ('rci', 'edp', 'addp', 'xbee'):
    logger = logging.getLogger(log_name)
    logger.addHandler(custom_handler)

class LogsHandler:
    def __call__(self, request):
        global logs
        if request.method == 'GET':
            response = []
            # copy logs in thread-safe way
            while logs:
                record = logs.pop(0)
                if not hasattr(record, 'asctime'):
                    record.asctime = time.ctime(record.created)
                response.append(record.__dict__)
            return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()
