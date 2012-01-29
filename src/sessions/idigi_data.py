"""\ 
iDigi Data Session

Include this session in your configuration to enable the automatic upload of
iDigi I/O Sample information to iDigi and the idigi_data: URL syntax to
upload data to the iDigi channelized data feed API.

iDigi I/O Sample information will be available from iDigi using your iDigi
account credentials at:

    http://(my|developer).idigi.com/ws/DiaChannelDataHistoryFull
or,
    http://(my|developer).idigi.com/ws/DiaChannelDataFull

With a ddInstanceName of XBee_AABBCC where AABBCC is the DL of your XBee
and a ddChannelName with the name of the I/O pin (e.g. "AD0").

You may also upload data to iDigi by using the following URL syntax:

    idigi_data:names=N1,N2,..Nn&values=V1,V2,..,VN,[units=U1,U2,..,Un]
    idigi_data:names=temp,humidity,alarm&values=21,40,False&units=C,RH%,bool

Where the entire name/value string is urlencoded (of type 
application/x-www-form-urlencoded).  Data will then appear on iDigi with
a ddInstanceName of XBee_AABBCC where AABBCC is the DL of the XBee the
data arrive from and a ddChannelNameset to NAME[0..N].

The idigi_data_max_rate_sec controls the number of seconds which must
elapse before sample batches are upload to iDigi.  This guard is set
to prevent the gateway from uploading too often and not having the time
to processing incoming data from the XBee network.
"""

import sys
import time
import threading
from cgi import parse_qs
from urllib import urlencode
from exceptions import OverflowError

from abstract_autostart import AbstractAutostartSession
from abstract import AbstractSession

import library.digi_ElementTree as ET
from library.helpers import iso_date
from library.io_sample import parse_is, sample_to_mv
import library.xbee_addressing as xbee_addressing

if sys.platform.startswith('digi'):
    import library.idigi_data as idigi_data

MAX_SAMPLE_Q_LEN = 256

def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True


class iDigiDataUploader(object):
    FILENAME_PREFIX="xig_"
    COLLECTION="xig_data"
    SECURE=False
    
    def __init__(self, xig_core, max_rate_sec, max_sample_q_len):
        self.__core = xig_core
        self.__max_rate_sec = max_rate_sec
        self.__max_sample_q_len = max_sample_q_len
        self.__sample_q = []
        self.__lock = threading.RLock()

    def sample_add(self, name, value, unit, timestamp):
        sample = { "name": name, "value": value, 
                   "unit": unit, "timestamp": timestamp }
        
        if len(self.__sample_q) > self.__max_sample_q_len:
            self.__sample_q.pop(0)
            
        self.__sample_q.append(sample)

    def __format_doc(self):
        doc = ET.Element("idigi_data")
        doc.set("compact", "True")
        
        for sample in self.__sample_q:
            elem = ET.Element("sample")
            map(lambda k: elem.set(k, sample[k]), sample.keys())
            doc.append(elem)
        
        return ET.ElementTree(doc).writestring()

    def upload(self):
        filename=(self.FILENAME_PREFIX + str(int(time.time())) + ".xml")
        try:
            self.__lock.acquire()
            try:
              idigi_data.send_idigi_data(self.__format_doc(),
                                         filename,
                                         self.COLLECTION, self.SECURE)
              print 'IDIGI_DATA: upload of %d samples successful' % \
                        len(self.__sample_q)
              self.__sample_q = []
            except Exception, e:
                print 'IDIGI_DATA: error during upload "%s"' % str(e)
        finally:
            self.__lock.release()


    def reschedule(self):
        self.__core.scheduleAfter(self.__max_rate_sec, self._sched_callback)

    def _sched_callback(self):
        try:
            if len(self.__sample_q) > 0:
                self.upload()
        finally:
            self.reschedule()
            
                

class iDigiDataAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        max_rate_sec = getattr(self.__core.getConfig(),
                               "idigi_data_max_rate_sec", 60)
        self.__uploader = iDigiDataUploader(xig_core,
                                            max_rate_sec, MAX_SAMPLE_Q_LEN)
        # kick off initial uploader scheduling task:
        self.__uploader.reschedule()
        self.__core.ioSampleSubcriberAdd(self.__ioSampleCallback)

    def helpText(self):
        return """\
 idigi_data running, uploading XBee I/O sample data to iDigi
"""

    def _sample_add(self, name, value, unit, timestamp):
        self.__uploader.sample_add(name, value, unit, timestamp)

    def __ioSampleCallback(self, buf, addr):
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
        dl_addr = xbee_addressing.normalize_address(addr[0])
        # [00:11:22:33:44:aa:bb:cc:dd]! -> XBee_AABBCCDD
        dl_addr = "XBee_" + ''.join(dl_addr.split(":")[4:])[:-3].upper()
        
        for io_pin in io_set.intersection(sample_set):
            unit = "bool"
            value = str(bool(int(sample[io_pin])))
            if io_pin in ad_set:
                unit = "int"
                value = str(int(sample[io_pin]))
            self._sample_add(dl_addr + "." + io_pin, value, unit, iso_date())


class iDigiDataSession(AbstractSession):  
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core
        self.__idigi_data_autostart = xig_core.getAutostartSessions(
                                            obj_type=iDigiDataAutostartSession)
        self.__xbee_addr = xbee_addr
        self.__write_buf = ""
        
        if not url.startswith("idigi_data:"):
            self.do_error('url does not start with "idigi_data:"')
            return
        
        qs = url.split(":")[1]
        try:
            qs = parse_qs(qs)
        except:
            self._do_error("unable to parse sample string")
            return
                
        if "names" not in qs:
            self._do_error('required keyword "names" not present')
        if "values" not in qs:
            self._do_error('required keyword "names" not present')

        dl_addr = xbee_addressing.normalize_address(xbee_addr[0])
        # [00:11:22:33:44:aa:bb:cc:dd]! -> XBee_AABBCCDD
        dl_addr = "XBee_" + ''.join(dl_addr.split(":")[4:])[:-3].upper()
        
        names_list = map(lambda n: dl_addr + "." + n,
                         qs["names"][0].split(','))            
        param_lists = [ names_list, qs["values"][0].split(',') ]

        if "units" in qs:
            param_lists.append(qs["units"][0].split(','))
        else:
            param_lists.append(['']*len(param_lists[0]))

        if not all(len(l) == len(param_lists[0]) for l in param_lists[1:]):
            self._do_error("not all lists the same length")
            return

        # prepare all timestamps for samples
        param_lists.append( len(param_lists[0])*[iso_date()] )

        # submit samples:
        for sample_params in zip(*param_lists):
            self.__idigi_data_autostart._sample_add(*sample_params)
            
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        
        if cmd_str.startswith("idigi_data:"):
            return iDigiDataSession(xig_core, cmd_str, xbee_addr)
        
        return None

    @staticmethod
    def commandHelpText():
        return """\
 idigi_data:names=N1,N2,..Nn&values=V1,V2,..,VN,[units=U1,U2,..,Un]: 
                upload data sample to iDigi data service
"""

    def _do_error(self, err_str):
        self.__write_buf = "Xig-Error: idigi_data " + err_str

    def close(self):
        return

    def isFinished(self):
        return len(self.__write_buf) == 0

    def getXBeeAddr(self):
        return self.__xbee_addr

    def getReadSockets(self):
        """Returns a list of active non-blocking socket objects which may be read"""
        return []

    def getWriteSockets(self):
        """Returns a list of active non-blocking socket objects which may be read"""
        return []
    
    def getSessionToXBeeBuffer(self):
        """Session contains data which needs to be written to XBee socket."""
        return self.__write_buf

    def getXBeeToSessionBuffer(self):
        """Session contains data which needs to be written to session socket."""
        return ""

    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]
