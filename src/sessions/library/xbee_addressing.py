"""\
    Helper functions to parse XBee addresses.
"""

# imports
from socket import *

def normalize_address(addr):
    """\
        Normalizes an extended address string.

        Returns a string, adding brackets if needed.

    """

    # self-addressed special case:
    if addr is None:
        return addr

    if not validate_address(addr):
        raise ValueError, "XBee address '%s' invalid" % addr    
    addr = "[" + addr[0:len(addr)-1].lower() + "]!"
        
    return addr


def addresses_equal(addr1, addr2):
    """\
        Checks to see if two addresses are equal to each other.

        Returns True if they are equal, False if they are not.

    """

    try:
        addr1, addr2 = normalize_address(addr1), normalize_address(addr2)
        return addr1 == addr2
    except:
        pass
    return False


def validate_address(addr):
    """
       Checks the validity of a given address string.

       Returns True if the given address is a valid address, False if it is not.

    """

    # self-addressed special case:
    if addr is None:
        return True

    try:
        addrinfo = getaddrinfo(addr, None)
        # Check the address family of the parsed address:
        if addrinfo[0][0] == AF_ZIGBEE:
            return True
    except:
        pass

    return False
