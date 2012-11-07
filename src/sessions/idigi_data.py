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
import logging
import time
import threading
from cgi import parse_qs

from abstract_autostart import AbstractAutostartSession
from abstract import AbstractSession

import library.digi_ElementTree as ET
from library.helpers import iso_date
from library.io_sample import parse_is

try:
    import idigidata                               # new style
except:
    pass

if (not 'idigidata' in sys.modules) or ('idigidata' in sys.modules and not hasattr(idigidata, 'send_to_idigi')):
    import library.idigi_data as idigidata_legacy  # old style

MAX_UPLOAD_RATE_SEC_DEFAULT = 60
MAX_SAMPLE_Q_LEN_DEFAULT = 512
SAMPLE_PAGE_SIZE = 2048

logger = logging.getLogger("xig.idigi_data")
logger.setLevel(logging.INFO)

import sys
if sys.version_info < (2, 5):
    # only needed with versions of Python < 2.5
    def all(iterable):
        for element in iterable:
            if not element:
                return False
        return True


def addr2iDigiDataLabel(addr_tuple):
    if addr_tuple[0][-1] == '!': #XBee address
        # [00:11:22:33:44:aa:bb:cc:dd]! -> XBee_AABBCCDD
        return "XBee_" + ''.join(addr_tuple[0].split(":")[4:])[:-2].upper()
    elif '.' in addr_tuple[0]: #IPv4 address
        # 192.168.0.1 -> IPv4_192_168_0_1
        return "IPv4_" + '_'.join(addr_tuple[0].split('.'))
    elif ':' in addr_tuple[0]: #IPv6 address
        # FE80::0:1 -> IPv6_FE80__0_1
        return "IPv6_" + '_'.join(addr_tuple[0].split(':'))
    else:
        # error
        raise Exception("Unrecognized addr: %s" % str(addr_tuple))


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
        try:
            self.__lock.acquire()
            if len(self.__sample_q) >= self.__max_sample_q_len:
                logger.warning('sample queue full (len=%d), dropping oldest sample' % (len(self.__sample_q)))
                self.__sample_q.pop(0)
    
            self.__sample_q.append(sample)
        finally:
            self.__lock.release()

    def __format_doc(self, sample_q):
        """\
        Format the given sample queue as an XML document string.
        """
        doc = ET.Element("idigi_data")
        doc.set("compact", "True")

        for sample in sample_q:
            elem = ET.Element("sample")
            map(lambda k: elem.set(k, sample[k]), sample.keys())
            doc.append(elem)



        return ET.ElementTree(doc).writestring()

    def __upload_err_recovery(self, prev_sample_q):
        """\
        Transfers the previous sample queue to the active sample queue,
        potentially dropping samples according to the queue length
        configuration.
        """
        try:
            self.__lock.acquire()
            new_sample_q = self.__sample_q
            self.__sample_q = prev_sample_q
            for sample in new_sample_q:
                self.sample_add(**sample)
        finally:
            self.__lock.release()

    def __do_upload(self, document):
        filename=(self.FILENAME_PREFIX + str(int(time.time() * 1000)) + ".xml")
        if 'idigidata' in sys.modules and hasattr(idigidata, 'send_to_idigi'):
            # new style
            result = idigidata.send_to_idigi(document,
                                     filename,
                                     self.COLLECTION, "text/plain", timeout=120)
            success, error, errmsg = result
            if not success:
                raise Exception, "idigidata error: %s" % repr(result)
        else:
            # old style
            idigidata_legacy.send_idigi_data(document,
                                     filename,
                                     self.COLLECTION, self.SECURE)

    def upload(self):
        try:
            self.__lock.acquire()
            prev_sample_q = self.__sample_q
            self.__sample_q = []
        finally:
            self.__lock.release()

        # We page the data upload here as to not overwhelm the iDigi Dia
        # ingest process.
        #
        # TODO: when iDigi creates a new DataPoint interface, change this to use
        #       the new, speedier interface.
        logger.info('total of %d samples to upload' % len(prev_sample_q))
        while len(prev_sample_q) > 0:
            logger.info('%s samples remain in queue' % len(prev_sample_q))
            document = self.__format_doc(prev_sample_q[:SAMPLE_PAGE_SIZE])
            try:
                self.__do_upload(document)
                logger.info('uploaded %d samples to iDigi' % len(prev_sample_q[:SAMPLE_PAGE_SIZE]))
                prev_sample_q = prev_sample_q[SAMPLE_PAGE_SIZE:]
            except Exception, e:
                logger.warning('error during upload "%s"' % str(e))
                self.__upload_err_recovery(prev_sample_q)
                break

    def reschedule(self, after_sec=0):
        self.__core.scheduleAfter(after_sec, self._sched_callback)

    def _sched_callback(self):
        sched_at = self.__max_rate_sec
        try:
            upload_time = time.time()
            if len(self.__sample_q) > 0:
                self.upload()
            upload_time = time.time() - upload_time
            sched_at = max(self.__max_rate_sec - upload_time, 0)
        finally:
            if (len(self.__sample_q)) > 0:
                logger.warning('will upload again in %d seconds' % (sched_at))
            self.reschedule(sched_at)



class iDigiDataAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        
        # Parse configuration parameters:
        max_rate_sec = getattr(self.__core.getConfig(),
                               "idigi_data_max_rate_sec", MAX_UPLOAD_RATE_SEC_DEFAULT)
        max_sample_q_len = getattr(self.__core.getConfig(),
                                   "idigi_data_max_q_len", MAX_SAMPLE_Q_LEN_DEFAULT)

        
        self.__uploader = iDigiDataUploader(xig_core,
                                            max_rate_sec, max_sample_q_len)
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
            logger.warning("__ioSampleCallback(): bad I/O sample format")
            return

        # build pin sets:
        ad_set = set(map(lambda d: "AD%d" % d, range(7)))
        dio_set = set(map(lambda d: "DIO%d" % d, range(13)))
        io_set = ad_set.union(dio_set)
        sample_set = set(sample.keys())

        count = 0
        for io_pin in io_set.intersection(sample_set):
            unit = "bool"
            value = str(bool(int(sample[io_pin])))
            if io_pin in ad_set:
                unit = "int"
                value = str(int(sample[io_pin]))
            self._sample_add(addr2iDigiDataLabel(addr) + "." + io_pin, value, unit,
                             iso_date(None, True))
            count += 1
        logger.debug('queued %d I/O samples for upload to iDigi' % count)


class iDigiDataSession(AbstractSession):
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core
        self.__idigi_data_autostart = xig_core.getAutostartSessions(
                                            obj_type=iDigiDataAutostartSession)
        self.__no_errors = getattr(self.__core.getConfig(), "idigi_data_no_errors", False)
            
        self.__xbee_addr = xbee_addr
        self.__write_buf = ""

        if not url.startswith("idigi_data:"):
            self._do_error('url does not start with "idigi_data:"')
            return
        
        if url.count("idigi_data:") > 1:
            # special case, malformed command buffer
            self._do_error("too many idigi_data: in command string")

        qs = url.split(":")[1]
        try:
            qs = parse_qs(qs)
        except:
            self._do_error("unable to parse sample string")
            return

        if "names" not in qs:
            self._do_error('required keyword "names" not present')
            return
        if "values" not in qs:
            self._do_error('required keyword "values" not present')
            return

        dl_addr = addr2iDigiDataLabel(xbee_addr)

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
        param_lists.append( len(param_lists[0])*[iso_date(None, True)] )

        # submit samples:
        for sample_params in zip(*param_lists):
            self.__idigi_data_autostart._sample_add(*sample_params)
        logger.debug('queued %d samples for upload to iDigi' % len(names_list))

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
 idigi_data:names=N1,N2,..Nn&values=V1,V2,..,VN&[units=U1,U2,..,Un]:
                upload data sample to iDigi data service
"""

    def _do_error(self, err_str):
        if self.__no_errors:
            return
        
        self.__write_buf = "Xig-Error: idigi_data " + err_str + "\r\n"

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

    def appendXBeeToSessionBuffer(self, buf):
        """Append data to be sent out to the session."""
        return

    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]
