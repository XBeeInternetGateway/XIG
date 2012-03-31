import json
import webob
import serial.tools.list_ports

class SerialPortsHandler:
    
    def __call__(self, request):
        if request.method == 'GET':
            # return list of serial ports
            com_ports = []
            for port, desc, port_type in serial.tools.list_ports.comports():
                com_ports.append(port)
            com_ports.sort()
            return webob.Response(json.dumps(com_ports), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()
