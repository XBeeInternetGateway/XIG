class Addr(str):
    """Generic Address class to store MAC and IP addresses"""

    NUM_BYTES = None
    DELIMITER = ":"
    BASE = 16
    BYTES_PER_SEGMENT = 1
    CHARS = {10: "0123456789",
             16: "0123456789abcdefABCDEF"}

    def __new__(cls, value = 0):   #value may be a string (with spacers), Addr, or int/long
        value_long = None
        value_str = None
        if isinstance(value, Addr):
            #will only need to create new object based on this one.
            value_long = value.value_long
            value_str = value
        elif isinstance(value, str):
            # convert to long and then back to string (will normalize string)
            value_long = cls.string_to_long(value)
            value_str = cls.long_to_string(value_long)
        elif isinstance(value, int):
            value_long = value
            value_str = cls.long_to_string(value_long)
        else:
            raise Exception("Unsupported value (%s) for %s" % (str(value), str(cls.__name__)))
        new_object = super(Addr, cls).__new__(cls, value_str)   #magic sauce
        new_object.value_long = value_long
        return new_object

    def __cmp__(self, other):
        if isinstance(other, int):
            return self.value_long.__cmp__(other)
        elif isinstance(other, Addr):
            return self.value_long.__cmp__(other.value_long)
        elif isinstance(other, str):
            return self.value_long.__cmp__(self.__class__.string_to_long(other))
        else:
            # try to create an instance of this class and compare to the integer value.
            return self.value_long.__cmp__(self.__class__(other).value_long)

    @classmethod
    def multiplier(cls):
        if cls.BYTES_PER_SEGMENT == 1:
            return 0x100
        elif cls.BYTES_PER_SEGMENT == 2:
            return 0x10000
        else:
            return 0x100 ** cls.BYTES_PER_SEGMENT

    @classmethod
    def strip_str(cls, value):
        "Strip off extra characters from string"
        # strip characters
        stripped_value = ""
        char_list = cls.CHARS[cls.BASE] #NOTE: more efficient to store this as a local variable
        if cls.DELIMITER:
            char_list = char_list + cls.DELIMITER
        for ch in value:
            if ch in char_list:
                stripped_value = stripped_value + ch
        return stripped_value

    @classmethod
    def string_to_long(cls, value):
        "Convert from string to Integer"
        value = cls.strip_str(value)
        value_num = 0
        multiplier = cls.multiplier() #NOTE: more efficient to store this as a local variable
        for num in (int(x, cls.BASE) for x in value.split(cls.DELIMITER)):
            value_num = value_num * multiplier + num
        return value_num

    @classmethod
    def long_to_string(cls, value):
        "Convert from Integer to string"
        mask = cls.multiplier() - 1
        if cls.BASE == 10:
            formatter = "%d"
        else:
            formatter = "%%0%dX" % (cls.BYTES_PER_SEGMENT*2)
        output = []
        for i in xrange(0, cls.NUM_BYTES, cls.BYTES_PER_SEGMENT):
            output.insert(0, formatter % ((value >> (i*8*cls.BYTES_PER_SEGMENT)) & mask))
        return (cls.DELIMITER or '').join(output)

    @classmethod
    def from_bin_string(cls, buf, big_endian = True): #default to network order
        "Convert from string to Integer"
        value_num = 0
        if big_endian:
            for i in xrange(cls.NUM_BYTES):
                value_num = value_num * 0x100 + ord(buf[i])
        else:
            for i in xrange(cls.NUM_BYTES-1, -1, -1):
                value_num = value_num * 0x100 + ord(buf[i])
        return cls(value_num)


class XBee_Addr(Addr):
    """XBee extended 64-bit address that is wrapped in a []!"""
    NUM_BYTES = 8

    @classmethod
    def long_to_string(cls, value):
        "Convert from Integer to string"
        # add "[]!" wrapper to value
        return "["+super(XBee_Addr, cls).long_to_string(value)+"]!"

class EUI64_Addr(Addr):
    """XBee extended 64-bit address"""
    NUM_BYTES = 8
    # NOTE: this class doesn't wrap address with a "[]!"

class XBee_Short_Addr(XBee_Addr):
    """XBee short 16-bit address that is wrapped in a []!"""
    NUM_BYTES = 2
    DELIMITER = None
    BYTES_PER_SEGMENT = 2


class Eth_MAC(Addr):
    NUM_BYTES = 6
    #TODO: this could use a '-' instead of ":"?


class IPv4_Addr(Addr):
    NUM_BYTES = 4
    BASE = 10
    DELIMITER = "."


class IPv6_Addr(Addr):
    NUM_BYTES = 16
    BYTES_PER_SEGMENT = 2

    @classmethod
    def string_to_long(cls, value):
        "Convert from string to Integer"
        value = cls.strip_str(value)
        if '::' in value:
            front, back = [x.split(':') for x in value.split('::')]
            if not front[0]:
                front = []
            if not back[0]:
                back = []
            ip_array = [int(x, 16) for x in front+['0']*(8-len(front)-len(back))+back]
        else:
            ip_array = [int(x, 16) for x in value.split(':')]
        value_num = 0
        multiplier = cls.multiplier() #NOTE: more efficient to store this as a local variable
        for num in ip_array:
            value_num = value_num * multiplier + num
        return value_num

    @classmethod
    def long_to_string(cls, value):
        "Convert from Integer to string"
        output = []
        # find the largest group of zeros for compression
        # for example: fe80:80:0:0:0:0:0:1 -> fe80:80::1
        # also: 0:0:0:0:0:0:0:1 -> ::1
        max_start = -1
        max_count = 0
        count = 0
        for i in xrange(7, -1, -1):
            section = (value >> (i*16))& 0xFFFF
            output.append('%X'%section)
            if section:
                # non-zero, reset count
                count = 0
            else:
                # zero, keep counting
                count += 1
                if count > max_count:
                    max_count = count
                    max_start = 8 - i - max_count
        if max_start != -1:
            start = output[:max_start]
            end = output[max_start+max_count:]
            if not start:
                start = ['']
            if not end:
                end = ['']
            output = start+['']+end
        return ':'.join(output)


class Addr_Tuple(tuple):
    MAP = ()
    def __new__(cls, iterative = None, **kwargs):
        value_list = list(iterative or [])
        for i in xrange(len(cls.MAP)):
            value = kwargs.get(cls.MAP[i])
            if i >= len(value_list):
                value_list.append(0) #default all values to Zero
            if value is not None:
                value_list[i] = value
        new_object = super(Addr_Tuple, cls).__new__(cls, value_list)   #magic sauce
        return new_object

    def __getattr__(self, name):
        return self[list(self.MAP).index(name)]


class XBee_Addr_Tuple(Addr_Tuple):
    MAP = ("address", "endpoint_id", "profile_id", "cluster_id", "options", "transmission_id")
    def __new__(cls, iterative=None, **kwargs):
        address = kwargs.get('address')
        if address is None and iterative:
            address = iterative[0]
        if address is not None:
            if isinstance(address, str):
                address = Addr.strip_str(address)
                if len(address) > 8:
                    # this is an extended address (EUI-64)
                    address = XBee_Addr(address)
                else:
                    # this is a short address
                    address = XBee_Short_Addr(address)
            kwargs['address'] = address
        return super(XBee_Addr_Tuple, cls).__new__(cls, iterative, **kwargs)


class IP_Addr_Tuple(Addr_Tuple):
    MAP = ("address", "port")
    def __new__(cls, iterative=None, **kwargs):
        address = kwargs.get('address')
        if address is None and iterative:
            address = iterative[0]
        if address is not None:
            if isinstance(address, str):
                if ':' in address:
                    # this is probably an IPv6 address
                    address = IPv6_Addr(address)
                elif '.' in address:
                    #this might be an IPv4 address or a domain name...
                    try:
                        address = IPv4_Addr(address)
                    except:
                        pass # probably a domain name instead
            kwargs['address'] = address
        return super(IP_Addr_Tuple, cls).__new__(cls, iterative, **kwargs)

#for addr in (IPv4_Addr('192.168.0.1'),
#             IPv6_Addr('fe80::1'),
#             XBee_Addr('00:11:22:33:44:55:66:77')):
#    print addr.__class__.__name__
#    print addr.value_long
#    print addr
#
#for ip_tuple in (IP_Addr_Tuple(("fe80::1", 80)),
#                 IP_Addr_Tuple(("10.10.80.1", 80))):
#    print ip_tuple.__class__.__name__
#    print ip_tuple.address
#    print ip_tuple.port
#    print ip_tuple
#
#for xbee_tuple in (XBee_Addr_Tuple(("00:11:22:33:44:55:66:77", 0x5e, 0x0109, 0x8000)),
#                   XBee_Addr_Tuple(("[00:11:22:33:44:55:66:77]!", 0x5e, 0x0109, 0x8000))):
#    print xbee_tuple.__class__.__name__
#    print xbee_tuple.address
#    print xbee_tuple.endpoint_id
#    print xbee_tuple.profile_id
#    print xbee_tuple.cluster_id
#    print xbee_tuple
