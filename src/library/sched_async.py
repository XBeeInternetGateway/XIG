############################################################################
#                                                                          #
# Copyright (c)2008, 2009, Digi International (Digi). All Rights Reserved. #
#                                                                          #
# Permission to use, copy, modify, and distribute this software and its    #
# documentation, without fee and without a signed licensing agreement, is  #
# hereby granted, provided that the software is used on Digi products only #
# and that the software contain this copyright notice,  and the following  #
# two paragraphs appear in all copies, modifications, and distributions as #
# well. Contact Product Management, Digi International, Inc., 11001 Bren   #
# Road East, Minnetonka, MN, +1 952-912-3444, for commercial licensing     #
# opportunities for non-Digi products.                                     #
#                                                                          #
# DIGI SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED   #
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A          #
# PARTICULAR PURPOSE. THE SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, #
# PROVIDED HEREUNDER IS PROVIDED "AS IS" AND WITHOUT WARRANTY OF ANY KIND. #
# DIGI HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,         #
# ENHANCEMENTS, OR MODIFICATIONS.                                          #
#                                                                          #
# IN NO EVENT SHALL DIGI BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,      #
# SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS,   #
# ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF   #
# DIGI HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.                #
#                                                                          #
############################################################################

"""
A threaded scheduler implementation that can be stopped asynchronously.

An instance of SchedAsync will create the scheduler.  The scheduler
manages a list of events to execute after a time interval has elapsed.  When
the scheduler is in-between events it will sleep.

This scheduler uses digi_sched which is based upon the
Python standard library's sched implementation.  If this scheduler
gets behind, it simply gets behind.  It offers no real-time guarantees.
"""

import digi_sched as sched
import threading
from copy import copy

import logging
logger = logging.getLogger("xig.sched_async")

# exception classes
class SchedulerBadCallback(Exception):
    """Exception raised when a bad callback is passed to schedule_after"""

class SchedAsync(threading.Thread):
    """
    Creates a new :class:`SchedAsync` instance.

    After the instance is created it must be started by calling the
    :meth:`start` function.
    """

    PRIORITY_HIGH = 16
    PRIORITY_NORMAL = 8
    PRIORITY_LOW = 0

    def __init__(self, name="scheduler", xig_core=None):
        self.__name = name
        self.__core = xig_core

        self.__semaphore = threading.Semaphore(0)
        self.__stop_flag = False

        self.__sched = sched.scheduler()

        threading.Thread.__init__(self)
        threading.Thread.setDaemon(self, True)

    def __new_event(self, delay, priority, action, args):
        if self.__stop_flag:
            return None

        event = self.__sched.enter(delay, priority, action, args)
        self.__semaphore.release()

        return event

    def __do_stop(self):
        self.__stop_flag = True

        for event in copy(self.__sched.queue):
            try:
                self.__sched.cancel(event)
            except ValueError:
                pass

    def start(self):
        """Called to start the scheduler thread."""
        threading.Thread.start(self)

    def stop(self):
        """Called to stop the scheduler thread.

        All pending events will be canceled.
        """
        self.__new_event(0, self.PRIORITY_HIGH, self.__do_stop, ())
        self.join(120)
        if self.isAlive():
            raise RuntimeError("Could not stop %s in time" % self.__name)
                
        return True

    def cancel(self, event_handle):
        """Cancel a given event given by `event_handle`.

        `event_handle` is the return value of an event scheduled by calling
        :meth:`schedule_after`.

        If the event cannot be found :exc:`ValueError` will be raised.
        """
        self.__sched.cancel(event_handle)

    def schedule_after(self, delay, action, *args):
        """Schedule an event.

        Returns an event handle.

        `delay` specifies the amount of seconds to wait before executing
        the function given by `action`.

        Following `action` are optional parameters which will be passed
        to the `action` function when the scheduled event becomes active.
        """

        if callable(action):
            return self.__new_event(delay, self.PRIORITY_NORMAL,
                                    action, args)
        else:
            raise SchedulerBadCallback, "Scheduled action is not callable"

        
    def run(self):
        """An internal method used by the :class:`SchedAsync` thread.
        
        This function is for internal use only.

        It also assumes that 'self' has a Tracer object attached at
        self.__tracer.
        """
        while not self.__stop_flag:
            self.__semaphore.acquire(blocking=True)
            try:
                self.__sched.run()
            except Exception, e:
                logger.error('caught exception: "%s"' % (str(e)))
