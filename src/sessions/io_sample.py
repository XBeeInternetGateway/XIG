"""\ 
I/O Sample Autostart Session

Include this session in your configuration to have the XIG
call remote URLs for each and every I/O sample packet it receives.


"""

import logging
from urllib import urlencode
from exceptions import OverflowError

from abstract_autostart import AbstractAutostartSession
from http import HTTPSession

from library.io_sample import parse_is

logger = logging.getLogger("xig.io_sample")
logger.setLevel(logging.INFO)

class ioSampleSessionAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__io_sample_destination_url = {}
        # get configuration values
        config_io_sample_destination_url = getattr(
            self.__core.getConfig(), "io_sample_destination_url", None)
        # normalize configuration to a dictionary:
        if not isinstance(config_io_sample_destination_url, dict):
            self.__default_destination_url = config_io_sample_destination_url
        else:
            self.__default_destination_url = config_io_sample_destination_url.pop('default', None)
            # normalize all XBee address keys in dictionary:
            for addr, url in config_io_sample_destination_url.iteritems():
                try:
                    xbee_addr = self.__core.xbeeAddrFromHwAddr(addr)
                    self.__io_sample_destination_url[xbee_addr] = url
                except:
                    logger.warning("ioSample: unable to normalize %s" % repr(addr))
        
        self.__core.ioSampleSubcriberAdd(self.__ioSampleCallback)

    def helpText(self):
        return """\
 io_sample running, making requests to configured destinations
"""

    def __ioSampleCallback(self, buf, addr_tuple):
        if self.__io_sample_destination_url is None:
            logger.info("__ioSampleCallback(): no URL configured.")
            return
        
        try:
            sample = parse_is(buf)
        except:
            logger.warning("__ioSampleCallback(): bad I/O sample format")
            return
        
        # build pin sets:
        ad_set = set(map(lambda d: "AD%d" % d, range(7)))
        dio_set = set(map(lambda d: "DIO%d" % d, range(13)))
        io_set = ad_set.union(dio_set)
        sample_set = set(sample.keys())
        
        # find appropriate I/O sample URL destination:
        dest_url = self.__io_sample_destination_url.get(addr_tuple.address, self.__default_destination_url)
        if not dest_url:
            # no url configured to send values
            return
            
        # built URL predicate:
        url_pred = { "addr": addr_tuple.address }
        for io_pin in io_set.intersection(sample_set):
            url_pred[io_pin] = str(int(sample[io_pin]))
        if "?" in dest_url:
            url_pred = urlencode(url_pred)
        else:
            url_pred = "?" + urlencode(url_pred)
        url = dest_url + url_pred
            
        # schedule HTTP session operation:
        http_session = HTTPSession(self.__core, url, addr_tuple, True)
        try:
            self.__core.enqueueSession(http_session)
        except OverflowError:
            return self.__xml_err_msg("queue full for destination")
