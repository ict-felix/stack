from db.db_manager import db_sync_manager
from core.config import ConfParser
from core.organisations import AllowedOrganisations
from extensions.sfa.util.xrn import hrn_to_urn, urn_to_hrn
from lxml import etree

import ast
import copy
import core
import re
import requests

logger = core.log.getLogger("monitoring-base")


class BaseMonitoring(object):
    """
    Base class for both physical and slice topology sent to the MS.
    """

    def __init__(self):
        super(BaseMonitoring, self).__init__()
        self.peers = [p for p in db_sync_manager.get_configured_peers()]
        self.domain_urn = ""
        self.domain_last_update = ""
        self.topology_list = etree.Element("topology_list")
        self.topology = etree.Element("topology")
        ## Operation mode
        self.config = ConfParser("ro.conf")
        master_ro = self.config.get("master_ro")
        self.mro_enabled = ast.literal_eval(master_ro.get("mro_enabled"))
        ## Dictionaries
        self.felix_organisations = AllowedOrganisations.get_organisations_type()
        self.software_stacks = {
                                "ofelia": "ocf",
                                "felix": "fms",
                                }
        self.urn_type_resources = {
                                "crm": "vtam",
                                "sdnrm": "openflow",
                                "serm": "se",
                                "tnrm": "tn",
                                }
        self.urn_type_resources_variations = {
                                "crm": ["vtam"],
                                "sdnrm": ["openflow", "ofam"],
                                "serm": ["se"],
                                "tnrm": ["tn", "NSI"],
                                }
        self.management_type_resources = {
                                "crm": "server",
                                "sdnrm": "switch",
                                "serm": "se",
                                }
        self.monitoring_expected_nodes = {
                                "crm": "",
                                "sdnrm": "switch",
                                "serm": "se",
                                "tnrm": "tn",
                                }
        self.peers_by_domain = {}
        self.__group_peers_by_domain()
        ## Configurations
        # CRM config
        self.config_crm = core.config.JSONParser("crm.json")
        self.crm_mgmt_info = self.config_crm.get("device_management_info")
        # SDNRM config
        self.config_sdnrm = core.config.JSONParser("sdnrm.json")
        self.sdnrm_mgmt_info = self.config_sdnrm.get("device_management_info")
        # SERM config
        self.config_serm = core.config.JSONParser("serm.json")
        self.serm_mgmt_info = self.config_serm.get("device_management_info")

    def __group_peers_by_domain(self):
        for peer in self.peers:
            filter_params = {"_ref_peer": peer.get("_id"),}
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            peer_domain_urn = domain_peer.get("domain_urn")
            authority = self._get_authority_from_urn(peer_domain_urn)
            # If authority (domain name) does not exist yet, create
            if not self.peers_by_domain.get(authority):
                self.peers_by_domain[authority] = []
            # Extend list of peers with new one
            self.peers_by_domain[authority].append(peer_domain_urn)
        # XXX: BEGIN TEMPORARY CODE FOR (M)MS
        # TODO: REMOVE THIS IN DUE TIME
        # Added so that (M)MS receives at least one TNRM per island
        type_resource_peer_tnrm = self.urn_type_resources_variations.get("tnrm")
        for peer in self.peers:
            filter_params = {"_ref_peer": peer.get("_id"),}
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            peer_domain_urn = domain_peer.get("domain_urn")
            peer_is_tnrm = any([rt in peer_domain_urn for rt in type_resource_peer_tnrm])
            # MRO: TNRM added at this level. Use information from peer to add it as a TNRM per domain
            if peer_is_tnrm:
                # Add the TNRM peer to each authority that does not have it yet
                for authority in self.peers_by_domain:
                    if peer_domain_urn not in self.peers_by_domain.get(authority):
                        self.peers_by_domain[authority].append(peer_domain_urn)
            # XXX: END TEMPORARY CODE FOR (M)MS

    def _send(self, xml_data, peer=None):
        try:
            if not peer:
                peer = self.monitoring_system

            url = "%s:%s/%s" % (peer.get("address"),
                                     peer.get("port"), peer.get("endpoint"))
            # Post-process URL to remove N slashes in a row
            url = re.sub("/{2,}", "/", url)
            # And add protocol (with 2 slashes)
            url = "%s://%s" % (peer.get("protocol"), url)
            logger.info("url=%s" % (url,))
            logger.info("data=%s" % (xml_data,))

            # NOTE This may require certificates or BasicAuth at some point
            reply = requests.post(url=url,
                                 headers={"Content-Type": "application/xml"},
                                 data=xml_data).text
            logger.info("Reply=%s" % (reply,))

        except Exception as e:
            logger.error("Could not connect to %s. Exception: %s" % (url, e,))


    ##########################
    # Set and return topology
    ##########################

    def set_topology_tree(self, topology_list_tree):
        # Return whole list of topologies
        try:
            ## If the following line works, 'topology_list_tree' is a proper xml tree
            topology_list_proper = etree.tostring(topology_list_tree)
            self.topology_list = topology_list_tree
        except:
            pass
            
    def get_topology_tree(self):
        # Return whole list of topologies
        return self.topology_list

    def get_topology(self):
        if self.get_topology_tree() is not None:
            return etree.tostring(self.get_topology_tree())

    def get_topology_pretty(self):
        # XML not in proper format: need to convert to lxml, then pretty-print
        return etree.tostring(etree.fromstring(self.get_topology()), pretty_print=True)


    ##########
    # Helpers
    ##########

    def _get_authority_from_urn(self, urn):              
        authority = ""
        hrn, hrn_type = urn_to_hrn(urn)
        # Remove leaf (the component_manager part)
        hrn_list = hrn.split(".")
        hrn = ".".join(hrn_list[:-1])
        for hrn_element in hrn_list:
            if hrn_element in self.felix_organisations:
                authority = hrn_element
                break
        return authority
    
    def _update_topology_name(self):
        filter_string = "[@last_update_time='%s']" % str(self.domain_last_update)
        filtered_nodes = self.get_topology_tree().xpath("//topology%s" % filter_string)
        # There should only be one
        filtered_nodes[0].set("name", str(self.domain_urn))
        self.get_topology_tree().xpath("//topology%s" % filter_string)[0].set("name", str(self.domain_urn))
    
    def _remove_empty_topologies(self, filter_name=None, filter_update_time=None):
        filter_string = ""
        if filter_name:
            filter_string += "[@name='%s']" % str(filter_name)
        if filter_update_time:
            filter_string += "[@last_update_time='%s']" % str(filter_update_time)
        topology_tree = etree.fromstring(self.get_topology())
        filtered_nodes = topology_tree.xpath("//topology%s" % filter_string)
        for filtered_node in filtered_nodes:
            # Remove any node whose length is 0 (=> no content inside)
            if list(filtered_node) == 0:
                filtered_node.get_parent().remove(filtered_node)
        
    def _get_management_data_devices(self, parent_node):
        configuration_data = {}
        if self.urn_type_resources.get("crm") in parent_node.get("id"):
            configuration_data = self.crm_mgmt_info
        elif self.urn_type_resources.get("sdnrm") in parent_node.get("id"):
            configuration_data = self.sdnrm_mgmt_info
        elif self.urn_type_resources.get("serm") in parent_node.get("id"):
            configuration_data = self.serm_mgmt_info
        return configuration_data

    def _add_management_section(self, parent_node):
        management = etree.Element("management")
#        resource_management_info = db_sync_manager.get_management_info(
#                                        component_id=parent_node.get("component_id"))
        management.set("type", "snmp")
        address = etree.SubElement(management, "address")
        address.text = ""
        port = etree.SubElement(management, "port")
        port.text = ""
        auth_id = etree.SubElement(management, "auth_id")
        auth_id.text = "public"
        auth_pass = etree.SubElement(management, "auth_pass")
        auth_pass.text = ""
        try:
            configuration_data = self._get_management_data_devices(parent_node)
            if configuration_data is not None:
                # Possible mismatch between URN of *RM that is configured in the *rm.json config file 
                # and the URN directly received from the RM. Issue a comprehensive warning here
                if not parent_node.get("id") in configuration_data.keys():
                    raise Exception("Mismatch between configuration device URN and received URN for URN='%s'. Please check the settings of your RMs under RO's configuration folder" 
                                        % parent_node.get("id"))
                address.text = configuration_data.get(parent_node.get("id")).get("ip")
                port.text = configuration_data.get(parent_node.get("id")).get("port")
                auth_id.text = configuration_data.get(parent_node.get("id")).get("snmp").get("id")
                auth_pass.text = configuration_data.get(parent_node.get("id")).get("snmp").get("password")
        except Exception as e:
            logger.warning("Physical monitoring. Cannot add management data on '%s'. Details: %s" % (etree.tostring(parent_node), e))
        return management

    def _add_generic_node(self, parent_tag, node, node_type):
        n = etree.SubElement(parent_tag, "node")
        n.set("id", node.get("component_id"))
        n.set("type", node_type)
        # Generate management section for node
        # This is only active for normal RO operation (MRO should
        # probably not send this information to MMS)
        # XXX In case it should, MRO would store the full topology_list
        # from each RO and send them to MMS
        if not self.mro_enabled:
            if node_type in self.management_type_resources.values():
                try:
                    management = self._add_management_section(n)
                    n.append(management)
                except Exception as e:
                    logger.warning("Physical topology - Cannot add management section. Details: %s" % e)
        return n

    def _translate_link_types(self):
#        topology_tree = etree.fromstring(self.get_topology())
#        filtered_links = topology_tree.xpath("//link")
        filtered_links = self.topology_tree.findall(".//link")
        for filtered_link in filtered_links:
            if filtered_link.get("link_type"):
                filtered_link.set("link_type", self._translate_link_type(filtered_link))
            elif filtered_link.get("type"):
                filtered_link.set("type", self._translate_link_type(filtered_link))
#        self.set_topology_tree(topology_tree)

    def _translate_link_type(self, link):
        # TODO - IMPORTANT FOR MS TO PARSE PROPERLY:
        #   Add others as needed in the future!
        default_type = "lan"
        
        ms_link_type_lan = "lan"
        ms_link_type_static_link = "static_link"
        ms_link_type_vlan_trans = "vlan_translation"
        link_type_translation = {
            "l2" : ms_link_type_lan,
            "l2 link": ms_link_type_lan,
            #"urn:felix+static_link": ms_link_type_static_link,
            "urn:felix+static_link": ms_link_type_lan,
#            "urn:felix+vlan_trans": ms_link_type_vlan_trans,
            "urn:felix+vlan_trans": ms_link_type_lan,
        }
        # Tries to get some attributes
        link_type = link.get("link_type", "")
        if not link_type:
            link_type = link.get("type", "")
        # Otherwise it uses a default value
        if not link_type:
            link_type = default_type
        else:
            link_type = link_type_translation.get(link_type.lower(), default_type)
        return link_type

    def _set_dpid_port_from_link(self, component_id, link):
        mod_link = copy.deepcopy(link)
        # Keep component_id for further processing and then
        # retrieve the 2nd part of the link URN (with the resources)
        # E.g. "eth1-00:10:00:00:00:00:00:01_1"
        # And extract the DPID's port from there
        urn_split = component_id.split("+link+")[1]
        if "datapath" in mod_link.get("source_id"):
            dpid_port = urn_split.split("-")[0].split("_")[1]
            new_id = "%s_%s" % (mod_link.get("source_id"), dpid_port)
            mod_link["source_id"] = new_id
        elif "datapath" in mod_link.get("dest_id"):
            dpid_port = urn_split.split("-")[1].split("_")[1]
            new_id = "%s_%s" % (mod_link.get("dest_id"), dpid_port)
            mod_link["dest_id"] = new_id
        return mod_link


    #################
    # C-RM resources
    #################

    def _add_com_info(self):
        # 1. Nodes
        nodes = [ n for n in db_sync_manager.get_com_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            logger.debug("com-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "server")
            # Output interfaces per server
            logger.debug("com-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = etree.SubElement(n, "interface")
                # NOTE this is extending the "interface" URN
                interface.set("id", "%s+interface+%s" % (n.get("id"), iface))
        # 2. Links
        links = [ l for l in db_sync_manager.get_com_links_by_domain(self.domain_urn) ]
        logger.debug("com-links=%s" % (links,))
        for link in links:
            self._add_com_link(link)

    def _add_com_link(self, link):
        logger.debug("com-links=%s" % (link,))
        l = etree.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.set("type", self._translate_link_type(link))
        links = link.get("links")
        for link_i in links:
            # Modify link on-the-fly to add the DPID port as needed
            link_i = self._set_dpid_port_from_link(link.get("component_id"), link_i)
            # Source
            iface_source = etree.SubElement(l, "interface_ref")
            iface_source.set("client_id", link_i.get("source_id"))
            # Destination
            iface_dest = etree.SubElement(l, "interface_ref")
            iface_dest.set("client_id", link_i.get("dest_id"))


    ###################
    # SDN-RM resources
    ###################

    def _add_sdn_info(self):
        # 1. Nodes
        datapaths = [ d for d in db_sync_manager.get_sdn_datapaths_by_domain(self.domain_urn) ]
        for dp in datapaths:
            logger.debug("sdn-datapath=%s" % (dp,))
            switch = self._add_generic_node(self.topology, dp, "switch")
            for p in dp.get("ports"):
                iface = etree.SubElement(switch, "interface")
                iface.set("id", "%s_%s" % (switch.get("id"), p.get("num")))
                port = etree.SubElement(iface, "port")
                port.set("num", p.get("num"))
        # 2. Links
        (sdn_links, fed_links) = [ l for l in db_sync_manager.get_sdn_links_by_domain(self.domain_urn) ]
        for sdn_link in sdn_links:
            logger.debug("sdn-link=%s" % (sdn_link,))
            self._add_sdn_link(sdn_link)
        for sdn_fed_link in fed_links:
            logger.debug("fed-sdn-link=%s" % (sdn_fed_link,))

    def _add_sdn_link(self, link):
        l = etree.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.set("type", self._translate_link_type(link))
        ports = link.get("ports")
        dpids = link.get("dpids")
        try:
            for dpid_port in zip(dpids, ports):
                iface = etree.SubElement(l, "interface_ref")
                dpid = dpid_port[0]["component_id"]
                port = dpid_port[1]["port_num"]
                iface.set("client_id", "%s_%s" % (dpid, port))
        except Exception as e:
            logger.warning("Physical topology - Cannot add SE interface %s. Details: %s" % (component_id,e))


    ##################
    # TN-RM resources
    ##################

    def _add_tn_info(self):
        # 1. Nodes
        nodes = [ d for d in db_sync_manager.get_tn_nodes_by_domain(self.domain_urn) ]
        # XXX: TEMPORARY CODE FOR (M)MS
        # TODO: REMOVE THIS IN DUE TIME
        # Added so that (M)MS receives at least one TNRM per island
#        nodes = [ d for d in db_sync_manager.get_tn_nodes() ]
        for node in nodes:
            logger.debug("tn-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "tn")
            # Output interfaces per node
            logger.debug("tn-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = etree.SubElement(n, "interface")
                interface.set("id", iface.get("component_id"))
#        # 2. Links
#        links = [ l for l in db_sync_manager.get_tn_links_by_domain(self.domain_urn) ]


    ##################
    # SE-RM resources
    ##################

    def _add_se_info(self):
        # 1. Nodes
        nodes = [ d for d in db_sync_manager.get_se_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            logger.debug("se-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "se")
            # Output interfaces per node
            logger.debug("se-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = etree.SubElement(n, "interface")
                # Parse the component_id to get URN of SE and the port per interface
                component_id = iface.get("component_id")
                try:
                    interface.set("id", component_id)
#                    interface.attrib["id"] = component_id.split("_")[0]
                    port = etree.SubElement(interface, "port")
                    port.set("num", component_id.split("_")[1])
                except Exception as e:
                    logger.warning("Physical topology - Cannot add SE interface %s. Details: %s" % (component_id,e))
        # 2. Links
        links = [ l for l in db_sync_manager.get_se_links_by_domain(self.domain_urn) ]
        logger.debug("se-links=%s" % (links,))
        for link in links:
            logger.debug("se-links=%s" % (link,))
            self._add_se_link(link)

    def _add_se_link(self, link):
        # Special case: links to be filtered in POST {(M)RO -> (M)MS}
        SE_FILTERED_LINKS = ["*"]
        interfaces_cid = [ i.get("component_id") for i in link.get("interface_ref") ]
        interface_cid_in_filter = [ f for f in SE_FILTERED_LINKS if f in interfaces_cid ]

        if not interface_cid_in_filter:
            l = etree.SubElement(self.topology, "link")
            # NOTE that this cannot be empty
            l.set("type", self._translate_link_type(link))
            links = link.get("interface_ref")
            for link in links:
                # SE link
                iface = etree.SubElement(l, "interface_ref")
                iface.set("client_id", link.get("component_id"))

