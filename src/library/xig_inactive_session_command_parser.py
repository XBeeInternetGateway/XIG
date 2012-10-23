'''
Created on Sep 4, 2011

@author: jordanh

The XigInactiveSessionCommandParser is the default command parser.

When there is no active sessions characters are accumulated into
an object instance of this class, parsed and delimited by CR or LF
characters by XBee address.

The output of this parser is used by the XigIOKernel in order to
feed complete commands to the various session classes.
'''

import logging
logger = logging.getLogger("xig.xsic")

class XigInactiveSessionCommandParser(object):
    def __init__(self, xig_core):
        self.__global_max_buf_size = xig_core.getConfig().global_max_buf_size
        self.__addr_cmd_buf_map = {}

    class XigInactiveSessionCommand(object):
        def __init__(self, command, addr):
            self.command = command
            self.addr = addr
        
    def parse(self, buf, addr):
        if addr not in self.__addr_cmd_buf_map:
            self.__addr_cmd_buf_map[addr] = ""
        cmd_buf = self.__addr_cmd_buf_map[addr] + buf

        if len(cmd_buf) > self.__global_max_buf_size:
            sidx = len(cmd_buf) - self.__global_max_buf_size
            cmd_buf = cmd_buf[sidx:]
            
        # normalize line-endings in buffer:
        cmd_buf = cmd_buf.replace("\r","\n").replace("\n\n","\n")
        
        # if no complete commands, return
        if '\n' not in cmd_buf:
            self.__addr_cmd_buf_map[addr] = cmd_buf
            return []
        
        # return all complete commands:
        cmds = [ ]
        try:
            split_cmd_buf = cmd_buf.split("\n")
            terminus = len(split_cmd_buf)
            if not cmd_buf.endswith("\n"):
                # the last command is not complete, do not process:
                terminus -= 1
            for cmd_str in split_cmd_buf[:terminus]:
                if not len(cmd_str):
                    continue
                cmds.append(self.XigInactiveSessionCommand(cmd_str, addr))
        except:
            logger.warning("Exception parsing command buffer, flushing.")
            self.__addr_cmd_buf_map[addr] = ""
            return [ ]
        
        if cmd_buf.endswith("\n"):
            # no more commands (optimization):
            self.__addr_cmd_buf_map[addr] = ""
        else:
            # find last incomplete command:
            self.__addr_cmd_buf_map[addr] = cmd_buf[cmd_buf.rfind("\n")+1:]

        return cmds
