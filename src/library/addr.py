class Addr(long):
    """Generic Address class to store MAC and IP addresses"""
    
    NUM_BYTES = None
    DELIMITER = ":"
    BASE = 16
    BYTES_PER_SEGMENT = 1
    
    def __new__(cls, value = 0):   #value may be a string (with spacers), Addr, or int/long
        if isinstance(value, Addr):
            pass #will only need to create new object based on this one.
        elif isinstance(value, str):
            return cls.from_string(value)
        new_object = super(Addr, cls).__new__(cls, value)   #magic sauce
        return new_object
    
    @classmethod
    def multiplier(cls):
        if cls.BYTES_PER_SEGMENT == 1:
            return 0x100
        elif cls.BYTES_PER_SEGMENT == 2:
            return 0x10000
        else:
            return 0x100 ** cls.BYTES_PER_SEGMENT
    
    @classmethod
    def from_string(cls, value):
        "Convert from string to Integer"
        value = value.strip()
        value_num = 0
        multiplier = cls.multiplier() #NOTE: more efficient to store this as a local variable
        for num in (int(x, cls.BASE) for x in value.split(cls.DELIMITER)):
            value_num = value_num * multiplier + num
        return cls(value_num)
    
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
    
    def __str__(self):
        mask = self.multiplier() - 1
        if self.BASE == 10:
            formatter = "%d"
        else:
            formatter = "%%0%dX" % (self.BYTES_PER_SEGMENT*2)
        output = []
        for i in xrange(0, self.NUM_BYTES, self.BYTES_PER_SEGMENT):
            output.insert(0, formatter % ((self >> (i*8*self.BYTES_PER_SEGMENT)) & mask))
        return (self.DELIMITER or '').join(output)

    def __repr__(self):
        return "'%s'"%str(self)

    def socket_str(self):
        return str(self)


class XBee_Addr(Addr):
    NUM_BYTES = 8
    
    @classmethod
    def from_string(cls, value):
        # strip off "[]!" from value
        value = value.strip().lstrip('[').rstrip('!').rstrip(']')
        return super(XBee_Addr, cls).from_string(value)
        #return Addr.from_string(cls, value)
        
    def socket_str(self):
        return "["+str(self)+"]!"

#alias for XBee Addr
EUI64_Addr = XBee_Addr


class XBee_Short_Addr(XBee_Addr):
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
    def from_string(cls, value):
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
        return cls(value_num)

    def __str__(self):
        output = []
        # find the largest group of zeros for compression
        # for example: fe80:80:0:0:0:0:0:1 -> fe80:80::1
        # also: 0:0:0:0:0:0:0:1 -> ::1
        max_start = -1
        max_count = 0
        count = 0
        for i in xrange(7, -1, -1):
            value = (self >> (i*16))& 0xFFFF
            output.append('%X'%value)
            if value:
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
        return self[self.MAP.index(name)]

    def socket_tuple(self):
        if isinstance(self[0], Addr):
            address = self[0].socket_str()
        else:
            address = str(self[0])
        return (address,) + self[1:]
    

class XBee_Addr_Tuple(Addr_Tuple):
    MAP = ("address", "endpoint_id", "profile_id", "cluster_id", "options", "transmission_id")
    def __new__(cls, iterative=None, **kwargs):
        address = kwargs.get('address')
        if address is None and iterative:
            address = iterative[0]
        if address is not None:
            if isinstance(address, str):
                address = address.strip()
                if len(address) > 8:
                    # this is an extended address (EUI-64)
                    address = EUI64_Addr(address)
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
                address = address.strip()
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

