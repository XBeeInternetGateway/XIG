"""\ 
I/O Sample Autostart Session

Include this session in your configuration to have the XIG
call remote URLs for each and every I/O sample packet it receives.


"""

from urllib import urlencode
from exceptions import OverflowError

from abstract_autostart import AbstractAutostartSession
from http import HTTPSession

from library.io_sample import parse_is
import library.xbee_addressing as xbee_addressing

class ioSampleSessionAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__io_sample_destination_url = getattr(
            self.__core.getConfig(), "io_sample_destination_url", None)
        # normalize configuration to a dictionary:
        if not isinstance(self.__io_sample_destination_url, dict):
            self.__io_sample_destination_url = {
                "default": self.__io_sample_destination_url }
        elif "default" not in self.__io_sample_destination_url:
            self.__io_sample_destination_url["default"] = None
        # normalize all keys in dictionary:
        for k in filter(lambda k: k != "default",
                        self.__io_sample_destination_url.keys()):
            v = self.__io_sample_destination_url[k]
            del(self.__io_sample_destination_url[k])
            try:
                norm_k = xbee_addressing.normalize_address(k)
                self.__io_sample_destination_url[norm_k] = v
            except:
                print "ioSample: unable to normalize %s" % repr(k)
        
        self.__core.ioSampleSubcriberAdd(self.__ioSampleCallback)

    def helpText(self):
        return """\
 io_sample running, making requests to configured destinations
"""

    def __ioSampleCallback(self, buf, addr):
        if self.__io_sample_destination_url is None:
            print "__ioSampleCallback(): no URL configured."
            return
        
        try:
            sample = parse_is(buf)
        except:
            print "__ioSampleCallback(): bad I/O sample format"
            return
        
        # build pin sets:
        ad_set = set(map(lambda d: "AD%d" % d, range(7)))
        dio_set = set(map(lambda d: "DIO%d" % d, range(13)))
        io_set = ad_set.union(dio_set)
        sample_set = set(sample.keys())
        
        # normalize received address:
        norm_addr = xbee_addressing.normalize_address(addr[0])
        
        # find appropriate I/O sample URL destination:
        dest_url = self.__io_sample_destination_url["default"]
        if norm_addr in self.__io_sample_destination_url:
            dest_url = self.__io_sample_destination_url[norm_addr]
                           
        # built URL predicate:
        url_pred = { "addr": norm_addr }
        for io_pin in io_set.intersection(sample_set):
            url_pred[io_pin] = str(int(sample[io_pin]))
        if "?" in dest_url:
            url_pred = urlencode(url_pred)
        else:
            url_pred = "?" + urlencode(url_pred)
        url = dest_url + url_pred
            
        # schedule HTTP session operation:
        http_session = HTTPSession(self.__core, url, addr, True)
        try:
            self.__core.enqueueSession(http_session)
        except OverflowError:
            return self.__xml_err_msg("queue full for destination")
