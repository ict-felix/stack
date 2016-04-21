from delegate.geni.v3.rspecs.tnrm.request_parser import TNRMv3RequestParser
from delegate.geni.v3.rspecs.commons_se import SELink
from delegate.geni.v3.rspecs.commons_tn import Node, Interface
import delegate.geni.v3.se_static_links_manager as SEStaticLinkManager
import core


class SERMv3RequestParser(TNRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3RequestParser, self).__init__(from_file, from_string)
        self.SEStaticLinkManager = SEStaticLinkManager.StaticLinkVlanManager()
        self.__sv = self.rspec.nsmap.get('sharedvlan')
        self.logger = core.log.getLogger("geniv3delegate")
        self.staticVlans = {}

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
                        manager_.attrib.get("name"))

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_

    def nodes(self, links=None):
        nodes_ = []
        for n in self.rspec.findall(".//{%s}node" % (self.none)):
            s_ = None
            sliver_ = n.find("{%s}sliver_type" % (self.none))
            if sliver_ is not None:
                s_ = sliver_.attrib.get("name")

            n_ = Node(n.attrib.get("client_id"),
                      n.attrib.get("component_manager_id"),
                      n.attrib.get("exclusive"), s_)

            for i in n.iterfind("{%s}interface" % (self.none)):
                i_ = Interface(i.attrib.get("client_id"))
                # Try if this is the old Rspec format
                svChildrenNumber = len(list(i.iterfind("{%s}link_shared_vlan" % (self.__sv))))

                ### Checking if there are "sharedvlan" tags (old RSpec format)
                if svChildrenNumber == 1:
                    self.logger.debug("Probably old RSpec format in \"<node ...>\"")
                    try:

                        for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                            
                            if sv.attrib.get("vlantag") == "0":
                                staticPort = i.attrib.get("client_id").split("_")[-1]
                                if staticPort in self.staticVlans:
                                    self.logger.debug("choosing static port VLAN")
                                    staticPortVlan = self.SEStaticLinkManager.chooseVlan(staticPort)
                                    self.staticVlans[staticPort] = staticPortVlan
                                i_.add_vlan(staticPortVlan,
                                            sv.attrib.get("name"))
                            else:
                                i_.add_vlan(sv.attrib.get("vlantag"),
                                            sv.attrib.get("name"))
                        n_.add_interface(i_.serialize())
                    # On Exception try new Rspec format
                    except:
                        for link in links:
                            pass

                ### Checking if "sharedvlan" tags are missing (new RSpec format)
                elif svChildrenNumber == 0:
                    self.logger.debug(">>>>> Probably new RSpec format in \"<node ...>\"")
                    clientId = i.attrib.get("client_id")
                    self.searchVlanForPort(clientId)
                    vlanInRspec = self.searchVlanForPort(clientId)
                    port = clientId.split("_")[-1]
                    if vlanInRspec == "0":
                        if port in self.staticVlans:
                            vlanInRspec = self.staticVlans[port]
                        else:
                            self.logger.debug("choosing static port VLAN")
                            staticPortVlan = self.SEStaticLinkManager.chooseVlan(port)
                            self.staticVlans[port] = staticPortVlan
                            vlanInRspec = staticPortVlan
                    i_.add_vlan(vlanInRspec, clientId + "+vlan")
                    n_.add_interface(i_.serialize())

                ### Checking if there are more than one "sharedvlan" tag for each Interface (invalid RSpec format)
                elif svChildrenNumber > 1:
                    self.logger.debug(">>>>> Invalid RSpec format. Too many <sharedvlan> tags in \"<node ...>\".")

            nodes_.append(n_.serialize())

        return nodes_


    def parseOldRspecFromat(self):

        try:
            sliceVlanPairs=[]
            for l in self.rspec.findall(".//{%s}link" % (self.none)):
                client_id = l.attrib["client_id"]
                vlanPairs=[]
                vlanPairs.append(client_id)
                for i in l.iterfind("{%s}interface_ref" % (self.none)):
                    singleVlanPair={}
                    singleVlanPair["vlan"] = i.attrib["{http://ict-felix.eu/serm_request}vlan"] # felix:vlan param
                    singleVlanPair["port_id"] = i.attrib["client_id"]
                    port = singleVlanPair["port_id"].split("_")[-1]
                    if singleVlanPair["vlan"] == "0":
                        if port in self.staticVlans:
                            singleVlanPair["vlan"] = self.staticVlans[port]
                        else:
                            self.logger.debug("choosing static port VLAN")
                            staticPortVlan = self.SEStaticLinkManager.chooseVlan(port)
                            self.staticVlans[port] = staticPortVlan
                            singleVlanPair["vlan"] = staticPortVlan
                    vlanPairs.append(singleVlanPair)
                sliceVlanPairs.append(vlanPairs)
            return sliceVlanPairs
        except:
            try:
                self.logger.debug(">>>> 2nd Gen Rspec")
                sliceVlanPairs=[]
                for l in self.rspec.findall(".//{%s}link" % (self.none)):
                    client_id = l.attrib["client_id"]
                    vlanPairs=[]
                    vlanPairs.append(client_id)
                    
                    for i in l.iterfind("{%s}interface_ref" % (self.none)):
                        singleVlanPair={}
                        port_id = i.attrib["client_id"]
                        singleVlanPair["port_id"] = port_id
                        port = singleVlanPair["port_id"].split("_")[-1]

                        for n in self.rspec.findall(".//{%s}node" % (self.none)):
                            for i in n.findall(".//{%s}interface[@client_id='%s']" % (self.none, port_id)):
                                vlan_element = i.find(".//{http://www.geni.net/resources/rspec/ext/shared-vlan/1}link_shared_vlan")
                                singleVlanPair["vlan"] = vlan_element.attrib["vlantag"]
                                if singleVlanPair["vlan"] == "0":
                                    if staticPort in self.staticVlans:
                                        self.logger.debug("choosing static port VLAN")
                                        staticPortVlan = self.SEStaticLinkManager.chooseVlan(staticPort)
                                        self.staticVlans[staticPort] = staticPortVlan
                                vlanPairs.append(singleVlanPair)  
                    sliceVlanPairs.append(vlanPairs)
                return sliceVlanPairs

            except:
                self.logger.debug(">>>> 2nd Gen Rspec - failed!")
                try:
                    self.logger.info("Trying new RSpec format")
                    sliceVlanPairs = self.parseNewRspecFormat()
                    return sliceVlanPairs
                except Exception as e:
                    self.logger.error("RSpec format not valid!")

                return None

    def getVlanPairs (self):
        sliceVlanPairs=[]
        
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
                client_id = l.attrib["client_id"]
                singleVlanPair = []
                if "?vlan" in client_id:
                    print ">>>>>> New RSpec format"
                    
                    srcDst = client_id.split("-")

                    src = srcDst[0].split("?vlan=")
                    dst = srcDst[1].split("?vlan=")

                    vlanIn = src[1]

                    prefix, portIn = src[0].split("_")
                    prefix, dpid = prefix.rsplit("+", 1)

                    vlanOut = dst[1]
                    portOut = dst[0].split("_")[1]


                    clientIdOldFormat = prefix + "+" + dpid + "_" + portIn + "_" + dpid + "_" + portOut

                    singleVlanPair.append(clientIdOldFormat)

                    ### Check if there's static link and choose static VLANs
                    if vlanIn == "0":
                        if portIn in self.staticVlans:
                            vlanIn = self.staticVlans[portIn]
                        else:
                            self.logger.debug("choosing static port VLAN")
                            staticPortVlan = self.SEStaticLinkManager.chooseVlan(portIn)
                            self.staticVlans[portIn] = staticPortVlan
                            vlanIn = staticPortVlan
                    if vlanOut == "0":
                        if portOut in self.staticVlans:
                            vlanOut = self.staticVlans[portOut]
                        else:
                            self.logger.debug("choosing static port VLAN")
                            staticPortVlan = self.SEStaticLinkManager.chooseVlan(portOut)
                            self.staticVlans[portOut] = staticPortVlan
                            vlanOut = staticPortVlan


                    singleVlanPairSrc = {}
                    singleVlanPairSrc["port_id"] = prefix + "+" + dpid + "_" + portIn
                    singleVlanPairSrc["vlan"] = vlanIn

                    singleVlanPair.append(singleVlanPairSrc)

                    singleVlanPairDst = {}
                    singleVlanPairDst["port_id"] = prefix + "+" + dpid + "_" + portOut
                    singleVlanPairDst["vlan"] = vlanOut

                    singleVlanPair.append(singleVlanPairDst)

                    print ">>>>>>>>   %s-%s <-> %s-%s" %(portIn, vlanIn, portOut, vlanOut)
                    print ">>>>>>>>  prefix: ", prefix
                    print ">>>>>>>>  dpid: ", dpid

                    sliceVlanPairs.append(singleVlanPair)


                else:
                    sliceVlanPairs = self.parseOldRspecFromat()
                    return sliceVlanPairs

        return sliceVlanPairs


    #TODO: refactor/rename this method when test passed
    def parseNewRspecFormat (self):
        sliceVlanPairs=[]
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            client_id = l.attrib["client_id"]
            vlanPairs=[]

            vlanTranslateData = client_id.split("+")[-1]
            (src, dst) = vlanTranslateData.split("-")

            prefix = client_id.rsplit('+', 1)[0]

            ### Parse source port/vlan ###
            srcDpid = src.split("?")[0].split("_")[0]
            srcPort = src.split("?")[0].split("_")[1]
            srcVlan = src.split("?")[1].split("=")[-1]

            if srcVlan == "0":
                if srcPort in self.staticVlans:
                    self.logger.debug("choosing static port VLAN")
                    staticPortVlan = self.SEStaticLinkManager.chooseVlan(srcPort)
                    self.staticVlans[srcPort] = staticPortVlan

            srcPortUrn = prefix + "+" + srcDpid + "_" + srcPort

            
            ### Parse destination port/vlan ###
            dstDpid = dst.split("?")[0].split("_")[0]
            dstPort = dst.split("?")[0].split("_")[1]
            dstVlan = dst.split("?")[1].split("=")[-1]

            if dstVlan == "0":
                if dstPort in self.staticVlans:
                    self.logger.debug("choosing static port VLAN")
                    staticPortVlan = self.SEStaticLinkManager.chooseVlan(dstPort)
                    self.staticVlans[dstPort] = staticPortVlan

            dstPortUrn = prefix + "+" + dstDpid + "_" + dstPort

            
            id = prefix + "+" + srcDpid + "_" + srcPort + "_" + dstDpid + "_" + dstPort
            vlanPairs.append(id)
            vlanPairs.append({"port_id" : srcPortUrn, "vlan" : srcVlan})
            vlanPairs.append({"port_id" : dstPortUrn, "vlan" : dstVlan})

            # Add source and destination port/vlan pair
            sliceVlanPairs.append(vlanPairs)

        return sliceVlanPairs

    def searchVlanForPort(self, portClientId):
        portsVlans = self.parseNewRspecFormat()
        for cross in portsVlans:
            for value in cross:
                if isinstance(value, dict) and value['port_id'] == portClientId:
                    return value['vlan']

    def getStaticVlans(self):
        return self.staticVlans


