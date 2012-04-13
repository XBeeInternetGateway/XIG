import sys
sys.path.insert(0, "./library/ext")
sys.path.insert(0, "./library/ext/cp4pc")
sys.path.insert(0, ".")

# need to import early (to overwrite socket and select)
import xbee

import webob
import time
from webob.dec import wsgify
import threading
import json
import logging

# WSGI handlers
import handlers.static
import handlers.index
import handlers.settings
import handlers.serial_ports
import handlers.xb
import handlers.idigi
import handlers.logs
import handlers.xig_console

DEFAULT_PORT = 8000 #random number

logging.getLogger('').addHandler(logging.StreamHandler(sys.__stdout__))
logger = logging.getLogger('xig.gui')

# application settings
from simulator_settings import settings

# XIG application
import xig

# rci code and handlers
import rci

# set the version from XIG
settings['version'] = xig.VERSION


class XigApp(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)
        self.xig = None
        self.power = "off"
        self.enable_xig = True
        self.static_handler = handlers.static.StaticHandler()
        self.index_handler = handlers.index.IndexHandler()
        self.settings_handler = handlers.settings.SettingsHandler()
        self.serial_ports_handler = handlers.serial_ports.SerialPortsHandler()
        self.xbee_handler = handlers.xb.XbeeHandler()
        self.idigi_handler = handlers.idigi.idigiHandler()
        self.logs_handler = handlers.logs.LogsHandler()
        self.xig_console_handler = handlers.xig_console.XigConsoleHandler()
        self.xig_console_handler.start() # this handler is a thread
        
        # register self as an HTTP handler
        rci.set_wsgi_handler(self)
        
        # make sure a local port is set
        settings.setdefault('local_port', DEFAULT_PORT)
           
    def run(self):
        while 1:
            try: 
                # make sure rci and xbee are connected
                if self.enable_xig and rci.connected() and xbee.ddo_get_param(None, "VR"):
                    self.xig = xig.Xig()
                    try:
                        # set port for xig_console_handler
                        self.xig_console_handler.port = self.xig.getConfig().xbee_udp_port
                    except:
                        pass
                    # start XIG running forever
                    self.xig.go()
            except Exception, e:
                logger.error("Exception when running XIG: %s" % e)
            self.xig_console_handler.port = None
            self.xig = None
            time.sleep(1)

    def get_power(self):
        if self.xig and self.enable_xig:
            return "on"
        else:
            return "off"

    def poll(self):
        power = self.get_power()
        if power != self.power:
            self.power = power
            return power
        else:
            return None

    def xig_handler(self, request):
        if request.method == 'GET':
            response = self.get_power()             
            return webob.Response(json.dumps(response), content_type='json')
        elif request.method == 'POST':
            state = request.POST.get('power', 'off')
            if state == "off":
                self.enable_xig = False
                response = "off"
                if self.xig:
                    self.xig.quit()
            else:
                self.enable_xig = True
                response = self.get_power()       
            return webob.Response(json.dumps(response), content_type='json')            
        else:
            return webob.exc.HTTPMethodNotAllowed()        
    
    def poll_handler(self, request):
        if request.method == 'GET':
            response = {}
            for key, handler in (('power', self),
                                 ('settings', self.settings_handler), 
                                 ('logs', self.logs_handler),
                                 ('serial_ports', self.serial_ports_handler),
                                 ('idigi', self.idigi_handler),
                                 ('xbee', self.xbee_handler),
                                 ('console', self.xig_console_handler)):
                data = handler.poll()
                if data is not None:
                    response[key] = data
            return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()        
        
    
    @wsgify
    def __call__(self, request):
        if request.path_info_peek() in ['s', 'static', 'favicon.ico']:
            # this is a static file request, return static file.
            return self.static_handler(request)
        elif request.path in ['/index.html', 'index', '/', '']:
            # request for the main webpage
            return self.index_handler(request)
        elif request.path in ['/settings']:
            return self.settings_handler(request)
        elif request.path in ['/serial_ports']:
            return self.serial_ports_handler(request)
        elif request.path in ['/xbee', '/Xbee', '/XBee']:
            return self.xbee_handler(request)
        elif request.path in ['/idigi']:
            return self.idigi_handler(request)
        elif request.path in ['/logs']:
            return self.logs_handler(request)
        elif request.path in ['/xig_console']:
            return self.xig_console_handler(request)        
        elif request.path in ['/xig']:
            return self.xig_handler(request)        
        elif request.path in ['/poll']:
            return self.poll_handler(request)        
        else:
            return webob.exc.HTTPNotFound()

if __name__ == "__main__":
    app = XigApp()
    app.start()
    
    url = "http://localhost:%d" % settings['local_port']
    
    # Make sure the app is serving
    while 1:
        try:
            import urllib2
            page = urllib2.urlopen(url, timeout=5.0)
        except urllib2.URLError, e:
            if e.reason.errno == 61:
                # Port not bound yet? Try again after a delay.
                time.sleep(1)
                continue
        except Exception, e:
            pass # try to open the webpage from a standard browser anyway
        break
    
    import webbrowser
    webbrowser.open(url)    

    # Important! This little bit of hidden window trickery will allow
    # the GUI to respond to O/S GUI events, e.g. allowing the OSX
    # icon to no state "Application Not Responding"
    import Tkinter as tk
    root = tk.Tk()
    root.withdraw()
    def idle_loop():
        root.after(100, idle_loop)
    root.after(100, idle_loop)
    root.mainloop()

