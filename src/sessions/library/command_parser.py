'''
Streaming Command Parser Helper Classes

Allows for session objects which receive data character by character, blocks,
or lines to easily match against a list of registered command names.

This module intentionally avoids the use of Python's re module which is
extremely expensive memory-wise on Digi ConnectPort gateways.

Created on Aug 31, 2011

@author: jordanh
'''

class Command(object):
    def __init__(self, command_str, callback):
        self.command_str = command_str
        self.callback = callback

class StreamingCommandParser(object):
    def __init__(self):
        self.__command_map = {}
        self.__match_table = []
        self.__buf = ""
    
    def __build_match_table_entry(self, command_str):
        for i in range(len(command_str)):
            if (len(self.__match_table)-1) < i:
                self.__match_table.append([])
            c = command_str[i]
            if c not in self.__match_table[i]:
                self.__match_table[i].append(c) 
    
    def register_command(self, command_obj):
        self.__command_map[command_obj.command_str] = command_obj
        self.__build_match_table_entry(command_obj.command_str)

    def __do_callback(self, match_str):
        command = self.__command_map[match_str]
        # call callback
        try:
            command.callback()
        except Exception, e:
            print 'CommandParser: error calling cb for cmd "%s": %s' % (
                    command.command_str, str(e))
       
    def parse(self, s):
        """\
        Parse a string against registered command, call callback
        on successful match.
        
        Returns string if input string does not match any partial
        commands.  Returns an empty string if string partially
        matches.
        """
        self.__buf += s
                
        return_buf = ""
        matches = []
        incomplete_match = False
        
        # as long as there are characters, keep checking the input buffer:
        while len(self.__buf) and not incomplete_match:
            match_buf = ""
            
            # generate indexes for longest potenial match:
            for i in range(min(len(self.__buf), len(self.__match_table))):
                # check against match table:
                if self.__buf[i] not in self.__match_table[i]:
                    # match failure, take all characters processed this far
                    # and move to return buffer
                    return_buf += match_buf + self.__buf[i]
                    self.__buf = self.__buf[i+1:]
                    break
                # character matches table entry, accumulate to match buffer:
                match_buf += self.__buf[i]
                # check if accumulated match buffer matches any commands:
                if match_buf in self.__command_map:
                    matches.append(match_buf)
                    self.__buf = self.__buf[len(match_buf):]
                    match_buf = ""
                    break
                # check if we've been through everything in the input buffer:
                if (i+1) == len(self.__buf):
                    # we may need to receive more characters in a subsequent
                    # call
                    incomplete_match = True 
                
        # for all matches, process callbacks:
        for match_str in matches:
            self.__do_callback(match_str)

        # return non-matching characters:
        return return_buf
