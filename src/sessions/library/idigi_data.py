"""idigi_data 
idigi_data provides an easy way for Digi device based python apps to 
push up data files to the iDigi server the device belongs to.
See idigi_pc.py to run on a PC.
"""
import sys  
sys.path.append("WEB/python/idigi_data.zip")

# iDigi is built into Digi devices. You need to be running python on a Digi
# device with firmware support for iDigi to use this module.
import cwm as _idigi

import digi_httplib as httplib
from mimetypes import guess_type

__all__= ["send_idigi_data", "send_idigi_data_with_type", "send_idigi_xml", "get_idigi_values"]

def send_idigi_data (data, filename, collection=None, secure=True):
    """
    Send data to the iDigi data server with the filename specified.

    Note the filename must be specified and will be used to store the
    document.  If the filename already exists in the database the
    existing file will be overwritten.

    A file extension will be used to guess the content type using mimetypes.
    For instance, file1.xml will be stored as XML.  file2.jpg will be saved as
    a JPEG.

    `collection` is an optional paramater specifying any subcollections that 
    the file should be stored in.  None means use the root collection for this
    device.  collections are specified without leading or trailing slashes ('/')
    and must be separated with a slash (directory like).  

    Example collection: my_collections/sensors/morning_readings

    By default, all data is transferred using an encrypted transfer.  If 
    an unencrypted transfer is desired, specify `secure=False`.

    Returns (success, error, errmsg):
    
       Success:
          True if successful, False if the upload failed.

       error: 
          status of transfer. If HTTP transport, http status is returned.
          Errors:                                                            
          100-510      HTTP errors (see httplib.py).                         
          10000        Data service is not available on this device
          
       errmsg:
          text associated with error
          
    """

    this_type, encoding = guess_type(filename)

    if this_type == None:
        raise ValueError("File extension not recognized")

    return _send_to_idigi (data, filename, collection, this_type, secure)

def send_idigi_data_with_type (data, filename, collection, content_type, secure=True):
    """
    Send data to the iDigi data server with the filename specified.

    Note the filename must be specified and will be used to store the
    document.  If the filename already exists in the database the
    existing file will be overwritten.

    The content type will be used to store the file.  The content must
    be a valid content type. Example: `text/xml`

    `collection` specifies any subcollections that the file should be
    stored in.  None means use the root collection for this device.
    collections are specified without leading or trailing slashes
    ('/') and must be separated with a slash (directory like).

    Example collection: my_collections/sensors/morning_readings

    By default, all data is transferred using an encrypted transfer.  If 
    an unencrypted transfer is desired, specify secure=False.

    Returns (success, error, errmsg):

       Success:
          `True` if successful, `False` if the upload failed.
          
       error: 
          status of transfer. If HTTP transport, http status is returned. 
          Errors:                                                         
          100-510      HTTP errors (see httplib.py).                      
          10000        Data service is not available on this device           
              
       errmsg:
          text associated with error
          
    """

    return _send_to_idigi (data, filename, collection, content_type, secure)

def send_idigi_xml (userXml, filename, collection=None, secure=True):
    """
    Send the xml string userXml to the data server with the filename specified.

    Note the filename must be specified and will be used to store the
    document.  If the filename already exists in the database the
    existing file will be overwritten.

    A file extension of .xml is recommended (for example: my_file.xml)

    `collection` is an optional paramater specifying any
    subcollections that the file should be stored in.  None means use
    the root collection for this device.  collections are specified
    without leading or trailing slashes ('/') and must be separated
    with a slash (directory like).

    Example collection: my_collections/sensors/morning_readings

    By default, all data is transferred using an encrypted transfer.
    If an unencrypted transfer is desired, specify secure=False.

    Returns (success, error, errmsg):
    
       Success:
          `True` if successful, `False` if the upload failed.
          
       error:  
          status of transfer. If HTTP transport, http status is returned.
          Errors:                                                        
          100-510      HTTP errors (see httplib.py).                         
          10000        Data service is not available on this device
          
       errmsg:
          text associated with error
          
    """
    this_type = 'text/xml'

    return _send_to_idigi (userXml, filename, collection, this_type, secure)

def _send_to_idigi (data, filename, collection, content_type, secure=True):
    if data == None or filename == None:
        return False
        
    try:    
        host, token, path, port, securePort = _idigi._get_ws_parms()
        
        if secure == True:
            host = "%s:%d" % (host, securePort)
        else:
            host = "%s:%d" % (host, port)   
            
    except:
        host, token, path = _idigi._get_ws_parms()
        hostSplit = host.split(":")
        port = hostSplit[1]
        
    if host == None or host[0] == ":" or token == None or path == None or \
           port == None or port == 0:
        
        err = 10000
        msg = "Data Service not available, check Remote Management configuration"
        return False, err, msg

    if collection == None:
        fullPath = path
    else:
        fullPath = path + "/" + collection

    if secure == True:
        con = httplib.HTTPSConnection(host)
    else:
        con = httplib.HTTPConnection(host)

    con.putrequest('PUT', '%s/%s' % (fullPath, filename))

    con.putheader('Content-Type', content_type)
    clen = len(data)
    con.putheader('Content-Length', `clen`)
    con.putheader('Authorization', 'Basic %s' % token)
    con.endheaders()
    con.send(data)

    response = con.getresponse()
    errcode = response.status
    errmsg = response.reason
    headers = response.msg
    con.close()

    if errcode != 200 and errcode != 201:  
        return False, errcode, errmsg
    else:  
        return True, errcode, errmsg


def get_idigi_values():
    """\
        Used to return the current runtime iDigi values and parameters.
    """
    return _idigi._get_ws_parms()
