import webob
import json

from simulator_settings import settings

class SettingsHandler:
    
    def __call__(self, request):
        if request.method == 'GET':
            key = request.GET.get('key')
            if key:
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
