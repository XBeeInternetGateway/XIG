'''
Streaming Command Parser Helper Classes

Allows for session objects which receive data character by character, blocks,
or lines to easily match against a list of registered command names.

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
    
    def parse(self, s):
        """\
        Parse a string against registered command, call callback
        on successful match.
        
        Returns string if input string does not match any partial
        commands.  Returns an empty string if string partially
        matches.
        """
        # accumulate our match buffer
        self.__buf += s
        
        
        return_buf = ""
        matches = []
        
        while len(self.__buf):
            match_buf = ""
            partial_match = True
            for i in range(min(len(self.__buf), len(self.__match_table))):
                match_buf += self.__buf[i]
                if match_buf in self.__command_map:
                    matches.append(match_buf)
                    self.__buf = self.__buf[len(match_buf):]
                    partial_match = False
                    break
                
                if self.__buf[i] not in self.__match_table[i]:
                    # match failure, take all characters processed this far
                    # and move to return buffer
                    partial_match = False
                    return_buf += match_buf
                    self.__buf = self.__buf[i+1:]
                    break
                
            if not partial_match:
                continue
            else:
                # partial match, we're done here
                break

        for match_str in matches:
            command = self.__command_map[match_str]
            # call callback
            try:
                command.callback()
            except Exception, e:
                print 'CommandParser: error calling cb for cmd "%s": %s' % (
                        command.command_str, str(e))
            # wipe the match buffer up to the match length:
        
        return return_buf
