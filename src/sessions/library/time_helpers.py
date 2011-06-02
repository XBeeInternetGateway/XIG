"""
Specific helper methods to help with the formatting of time.
"""

import time

def _local_time_offset(t=None):
    """Return offset of local zone from GMT, either at present or at time t."""
    
    if 'timezone' in dir(time):
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

    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    
    if lto is not None:
        time_str += "%+03d:%02d" % (lto//(60*60), lto%60)

    return time_str
