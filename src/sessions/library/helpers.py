'''
Created on Jan 19, 2012

@author: jordanh
'''

import time

def _local_time_offset(t=None):
    """Return offset of local zone from GMT, either at present or at time t."""
    # python2.3 localtime() can't take None

    # ConnectPort Xs don't have an RTC, so we need to check for that
    # functionality first.
    if getattr(time, 'timezone', None) is not None:
        if t is None:
            t = time.time()

        if time.localtime(t).tm_isdst > 0 and time.daylight:
            return -time.altzone
        else:
            return -time.timezone

    else:
        return None


def iso_date(t=None, use_local_time_offset=False):
    """
    Return an ISO-formatted date string from a provided date/time object.
    
    Arguments:

    * `t` - The time object to use.  Defaults to the current time.
    * `use_local_time_offset` - Boolean value, which will adjust
        the ISO date by the local offset if set to `True`. Defaults
        to `False`.
          
    """
    if t is None:
        t = time.time()

    lto = None
    if use_local_time_offset:
        lto = _local_time_offset()

    # For example: 2012-09-23T10:58:30-05:00
    time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))
    
    if lto is not None:
        time_str += "%+03d:%02d" % (lto//(60*60), lto%60)
    else:
        # if no timezone, assume UTC
        time_str += "+00:00"

    return time_str
