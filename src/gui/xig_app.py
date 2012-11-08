#!/usr/bin/env python2.7

import sys
sys.path.insert(0, "./library/ext")
sys.path.insert(0, "./library/ext/cp4pc")
sys.path.insert(0, "./")

if sys.version_info < (2, 7):
    # should be run with Python version 2.7 or greater
    raise Exception("Must use Python 2.7 or greater.")

# need to import early (to overwrite socket and select)
import xbee

import argparse
import webob
import time
from webob.dec import wsgify
import threading
import json
import logging

import subprocess
import uuid


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

# setup stderr logging:
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(name)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

logger = logging.getLogger('xig.gui')

# application settings
from simulator_settings import settings

# XIG application
import xig

# rci code and handlers
import rci

# set the version from XIG
settings['version'] = xig.VERSION
settings['device_type'] = "XIG PC Gateway"

# global state
quit_flag = False


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

	if sys.platform == 'darwin':
	# special settings handling for OSX
	    self.__osx_settings()

	# add callbacks to restart XIG if serial port changes
	settings.add_callback('com_port', lambda new, old: self.xig_quit())
	settings.add_callback('baud', lambda new, old: self.xig_quit())

    def __osx_settings(self):
	p1 = subprocess.Popen(['/usr/sbin/ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], stdout=subprocess.PIPE)
	p2 = subprocess.Popen(['grep', 'IOPlatformUUID'], stdin=p1.stdout, stdout=subprocess.PIPE)
	output = p2.communicate()[0]
	darwin_uuid = output[output.find(' = "')+4:output.rfind('"')].strip()
	logger.info("Mac UUID is %s" % repr(darwin_uuid))
	set_darwin_uuid = settings.get('darwin_uuid', '')
	if darwin_uuid != set_darwin_uuid:
	    logger.info("Mac UUID changed, updating MAC and iDigi Device ID")
	    settings['darwin_uuid'] = darwin_uuid
	    settings['mac'] = uuid.getnode()
	    settings['device_id'] = "00000000-00000000-%06XFF-FF%06X" % ((settings.get('mac', 0x000000000000) & 0xFFFFFF000000) >> (8*3),
									  settings.get('mac', 0x000000000000) & 0x0000000FFFFFF)


    def xig_quit(self):
	if self.xig:
	    self.xig.quit()

    def run(self):
        global quit_flag
        
    	while not quit_flag:
    	    # make sure rci and xbee are connected
    	    try:
                if self.enable_xig and rci.connected() and xbee.ddo_get_param(None, "VR"):
                    try:
                        self.xig = xig.Xig()
                        try:
                            # set port for xig_console_handler
                            self.xig_console_handler.port = self.xig.getConfig().xbee_udp_port
                        except:
                            pass
                        # start XIG running forever unless a user quit was issued (status == 0)
                        status = self.xig.go()
                        if status == 0:
                            logger.info("Shutting down XIG GUI...")
                            self.enable_xig = False
                            time.sleep(5)
                            quit_flag = True
                    except Exception, e:
                        logger.error("Exception when running XIG: %s" % e)
            except:
                pass # expected exception when ddo_get_param fails
            self.xig_console_handler.port = None
            self.xig = None
            time.sleep(1)

    def get_power(self):
	if self.xig and self.enable_xig:
	    return "on"
	else:
	    return "off"

    def poll(self, refresh=False):
	power = self.get_power()
	if refresh or power != self.power:
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
		self.xig_quit()
	    else:
		self.enable_xig = True
		response = self.get_power()
	    return webob.Response(json.dumps(response), content_type='json')
	else:
	    return webob.exc.HTTPMethodNotAllowed()

    def poll_handler(self, request):
	if request.method == 'GET':
	    refresh = bool(request.GET.get('refresh', False))
	    response = {}
	    for key, handler in (('power', self),
				 ('settings', self.settings_handler),
				 ('logs', self.logs_handler),
				 ('serial_ports', self.serial_ports_handler),
				 ('idigi', self.idigi_handler),
				 ('xbee', self.xbee_handler),
				 ('console', self.xig_console_handler)):
		data = handler.poll(refresh)
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
    # Parse command line options:
    parser = argparse.ArgumentParser(description="XBee Internet Gateway (XIG) with Web GUI.")
    parser.add_argument('--no-browser', dest="no_browser", action="store_true",
			help="do not launch the web browser")
    args = parser.parse_args()

    # Start the app:
    app = XigApp()
    app.setDaemon(True)
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

    if not args.no_browser:
        # launch the web browser:
        import webbrowser
        webbrowser.open(url)

    # Important! This little bit of hidden window trickery will allow
    # the GUI to respond to O/S GUI events, e.g. allowing the OSX
    # icon to not state "Application Not Responding"
    sleepyTime = False
    try:
        import Tkinter as tk
        root = tk.Tk()
        root.withdraw()
        def idle_loop():
            if quit_flag:
                root.quit()
            root.after(250, idle_loop)
        root.after(250, idle_loop)
        root.mainloop()
    except ImportError:
        logger.warning("Tkinter not available, running as command-line only.")
        sleepyTime = True
    except tk._tkinter.TclError:
        logger.info("No window manager available, will run as command-line only.")
        sleepyTime = True

    # Prevent daemon threads from exiting
    if sleepyTime:
        while not quit_flag:
            time.sleep(1)

