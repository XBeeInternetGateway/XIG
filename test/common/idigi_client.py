
import httplib
import base64

class iDigiClient(object):
    def __init__(self, username, password, server="developer.idigi.com"):
        self.username = username
        self.password = password
        self.server = server

        self.__auth = base64.encodestring("%s:%s"%(username,password))[:-1]

    def post_request(self, path, message):
        webservice = httplib.HTTP(self.server, 80)
        webservice.putrequest("POST", path)
        webservice.putheader("Authorization", "Basic %s" % self.__auth)
        webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
        webservice.putheader("Content-length", "%d" % len(message))
        webservice.endheaders()
        webservice.send(message)

        # get the response
        statuscode, statusmessage, header = webservice.getreply()
        response_body = webservice.getfile().read()

        return response_body


    def get_request(self, path):
        webservice = httplib.HTTP(self.server, 80)
        webservice.putrequest("GET", path)
        webservice.putheader("Authorization", "Basic %s" % self.__auth)
        webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
        webservice.endheaders()

        # get the response
        statuscode, statusmessage, header = webservice.getreply()
        response_body = webservice.getfile().read()

        return response_body

