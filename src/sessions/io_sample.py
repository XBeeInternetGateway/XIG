"""\ 
I/O Sample Autostart Session

Include this session in your configuration to have the XIG
call remote URLs for each and every I/O sample packet it receives.


"""

from urllib import urlencode
from exceptions import OverflowError

from abstract_autostart import AbstractAutostartSession
from abstract import AbstractSession
from http import HTTPSession

from library.io_sample import parse_is, sample_to_mv

class ioSampleSessionAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__io_sample_destination_url = getattr(
            self.__core.getConfig(), "io_sample_destination_url", None)
        if not self.__io_sample_destination_url.endswith("/"):
            self.__io_sample_destination_url += "/"
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
        
        # convert all analog io pin values to voltages:
        for io_pin in ad_set.intersection(sample_set):
            sample[io_pin] = sample_to_mv(sample[io_pin])
        
        # built URL predicate:
        url_pred = { "addr": addr[0] }
        for io_pin in io_set.intersection(sample_set):
            url_pred[io_pin] = str(int(sample[io_pin]))
        url_pred = "?" + urlencode(url_pred)
        url = self.__io_sample_destination_url + url_pred
            
        # schedule HTTP session operation:
        http_session = HTTPSession(self.__core, url, addr, True)
        try:
            self.__core.enqueueSession(http_session)
        except OverflowError:
            return self.__xml_err_msg("queue full for destination")
