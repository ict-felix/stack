from vt_manager_kvm.models import *
from vt_manager_kvm.communication.util.XmlUtil import *
import xmlrpclib

xml = xmlFileToString('../agents/utils/xml/response.xml')
o = XmlHelper.parseXmlStringResponse(xml)
server = xmlrpclib.Server('https://expedient:expedient@192.168.254.193:8445/xmlrpc/agent')
server.sendAsync(xml)

