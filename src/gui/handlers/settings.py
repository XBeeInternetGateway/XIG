import webob
import json

from simulator_settings import settings

class SettingsHandler:
    
    def __init__(self):
        self.callbacks = {} # key, callback
        self.poll_data = {} # key, value
    
    def callback(self, key, new_value, old_value):
        self.poll_data[key] = new_value
    
    def poll(self, refresh=False): #NOTE: refresh not used.
        poll_data = self.poll_data
        self.poll_data = {}
        return poll_data or None
    
    def __call__(self, request):
        if request.method == 'GET':
            key = request.GET.get('key')
            if key:
                notify = request.GET.get('notify')
                if notify is not None:
                    if notify and notify not in self.callbacks:
                        # add a notify callback
                        callback = lambda new_value, old_value, key=key: self.callback(key, new_value, old_value)
                        settings.add_callback(key, callback)
                        self.callbacks[key] = callback
                    elif not notify and notify in self.callbacks:
                        # remove callback
                        settings.remove_callback(key, self.callbacks[key])
                        del self.callbacks[key]
                # return the value of a setting
                value = str(settings.get(key, ''))
                return webob.Response(json.dumps(value), content_type='json')
            else:
                # return all of the keys
                return webob.Response(json.dumps(settings), content_type='json')
        if request.method == 'POST':
            # set a value
            key = request.POST.get('key')
            if key:
                value = request.POST.get('value')
                # remove the setting if no value is given
                if value is None or value == 'undefined':
                    settings.pop(key, None)
                # figure out if the value is an int
                try:
                    value = int(value)
                except:
                    try:
                        value = float(value)
                    except:
                        pass
                # set the value
                settings[key] = value
                return #success
        else:
            return webob.exc.HTTPMethodNotAllowed()
