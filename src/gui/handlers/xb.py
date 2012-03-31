import webob
import json
import zigbee as xbee

def binstring_to_int(value):
    """
    Converts a big-endian binary string into an integer.
    """
    retval = 0
    #eat string starting from the first (most signficant) byte
    for curr_byte in value:
        retval = retval * 256 + ord(curr_byte)
    return retval

class XbeeHandler:

    AI_STATUS = {0x00 : "Joined or Formed Network",
                 0x21 : "No valid PANs",
                 0x22 : "No valid PANs",
                 0x23 : "Not allowing joining",
                 0x24 : "No joinable beacons",
                 0x25 : "Unexpected state",
                 0x27 : "Joining attempt failed",
                 0x2A : "Coordinator Start failed",
                 0x2B : "Checking for coordinator",
                 0x2C : "Leave network failed",
                 0x30 : "Discovering CBKE endpoint",
                 0x31 : "CBKE discovery failed",
                 0x32 : "CBKE Initiate missing",
                 0x33 : "CBKE Ephemeral data missing",
                 0x34 : "CBKE Confirm key missing",
                 0x36 : "Received terminate request",
                 0x3A : "CBKE transmission failed",
                 0x3B : "CBKE Invalid certificate",
                 0x3C : "CBKE not allowed",
                 0xAB : "Device did not respond",
                 0xAC : "Unsecured network key",
                 0xAD : "No network key",
                 0xAF : "Wrong link key",
                 0xFF : "Scanning..."  }

    
    def __call__(self, request):
        if request.method == 'GET':
            addr = request.GET.get('addr', None)
            at = request.GET.get('at')
            if at:
                if at == "status":
                    # read AI and return string value
                    try:
                        ai = ord(xbee.ddo_get_param(addr, 'ai'))
                    except Exception, e:
                        return webob.Response(json.dumps("XBee Not Connected."), content_type='json')
                    return webob.Response(json.dumps(self.AI_STATUS.get(ai, '0x%02X - Unknown Status' % ai)), content_type='json')
                elif at == "eui":
                    # read SH and SL and return a EUI-64
                    try:
                        eui = ":".join("%02X"%ord(x) for x in xbee.ddo_get_param(addr, 'sh') + xbee.ddo_get_param(addr, 'sl'))
                    except:
                        eui = ""
                    return webob.Response(json.dumps(eui), content_type='json')
                else:
                    # read AT parameter to return value
                    at_str = xbee.ddo_get_param(addr, at)
                    return webob.Response(json.dumps(binstring_to_int(at_str)), content_type='json')
            else:
                # invalid request
                return webob.exc.HTTPBadRequest()
        if request.method == 'POST':
            addr = request.POST.get('addr')
            at = request.POST.get('at')
            value = request.POST.get('value')
            if at is not None and value is not None:
                response = xbee.ddo_set_param(addr, at, value)
                return webob.Response(json.dumps(response), content_type='json')
        else:
            return webob.exc.HTTPMethodNotAllowed()

