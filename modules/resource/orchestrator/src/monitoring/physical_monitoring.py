from db.db_manager import db_sync_manager
from monitoring.base_monitoring import BaseMonitoring

import core
import traceback
from lxml import etree
from copy import deepcopy
from core.utils.urns import URNUtils

logger = core.log.getLogger("monitoring-physical")


class PhysicalMonitoring(BaseMonitoring):
    """
    Periodically communicates physical topology to the MS.
    """

    def __init__(self):
        super(PhysicalMonitoring, self).__init__()

    def retrieve_topology_by_peer(self, peer_urn):
        # Prepare list of allowed peers and resources
        type_resources_crm = ["crm"]
        type_resources_crm.extend(
            self.urn_type_resources_variations.get("crm"))
        type_resources_sdnrm = ["sdnrm"]
        type_resources_sdnrm.extend(
            self.urn_type_resources_variations.get("sdnrm"))
        type_resources_serm = ["serm"]
        type_resources_serm.extend(
            self.urn_type_resources_variations.get("serm"))
        type_resources_tnrm = ["tnrm"]
        type_resources_tnrm.extend(
            self.urn_type_resources_variations.get("tnrm"))

        type_resources = []
        type_resources.extend(type_resources_crm)
        type_resources.extend(type_resources_sdnrm)
        type_resources.extend(type_resources_serm)
        type_resources.extend(type_resources_tnrm)

        # If the URN belongs to one of those
        # peers/domains, add the information
        type_resource_peer = None
        for type_resource in type_resources:
            if type_resource in peer_urn:
                type_resource_peer = type_resource
                break
        # COM resources
        if type_resource_peer in type_resources_crm:
            self._add_com_info()
        # SDN resources
        elif type_resource_peer in type_resources_sdnrm:
            self._add_sdn_info()
        # TN resources (fix in URN...)
        elif type_resource_peer in type_resources_tnrm:
            self._add_tn_info()
        # SE resources
        elif type_resource_peer in type_resources_serm:
            self._add_se_info()

    def send_topology(self, monitoring_server):
        logger.debug("Configured peers=%d" % (len(self.peers)))
        for domain_name in self.peers_by_domain:
            self.__update_topology_per_domain(domain_name)
            # XXX: (M)MS expects to receive one TNRM per island
            if not self.__check_node_in_topology("tn"):
                self._add_tn_info()

            # Verify structure of the "topology" tag before
            # constructing final XML to be sent to MS
            # - Note: on SUCCESS return, it returns a boolean.
            # - On FAILURE return, it returns (boolean, string)
            check_topology = self.__check_topology_is_correct()
            if check_topology is True:
                self.flush_topology()
            else:
                logger.warning("Physical topology - Topology for domain=%s \
                does not contain the minimum SW modules required by MS: \
                missing '%s' node." % (domain_name, check_topology[1]))

        # Clean any empty node (result of not containing
        # the minimum SW modules)
        self.remove_empty_nodes()
        # M-RO environment: refactoring of the topology list
        # (regroup nodes & links per island)
        if self.mro_enabled:
            self.__group_resources_per_island()
        # Send topology after all peers are completed
        self._send(self.get_topology(), monitoring_server)
        logger.debug("Resulting RSpec=%s" % self.get_topology_pretty())

    ##########
    # Helpers
    ##########

    def __add_general_info(self):
        """
        Creates new RSpec from scratch.
        """
        # Milliseconds in UTC format
        self.topology.set(
            "last_update_time",
            self.domain_last_update or self._get_timestamp())
        self.topology.set("type", "physical")
        # Use custom URN format for the domain URN in the XML
        self.topology.set("name", "urn:publicid:IDN+ocf:" + self.domain_urn)

    def __check_node_in_topology(self, node_name):
        """
        Checks that the "<topology>" subtree contains a given node.
        """
        if not self.topology.findall(".//node[@type='%s']" % node_name):
            return False
        return True

    def __check_topology_is_correct(self):
        """
        Checks that the "<topology>" subtree contains all
        the required "<node>" tags (i.e. types) expected by MS.
        """
        # Remove unexpected / non-required nodes
        ms_expected_nodes = filter(
            lambda n: n,
            self.monitoring_expected_nodes.values())
        for n in ms_expected_nodes:
            # If any is not found, return false
            if not self.topology.findall(".//node[@type='%s']" % n):
                return (False, n)
        return True

    def __update_topology_per_domain(self, domain_name):
        try:
            peers = self.peers_by_domain[domain_name]
            # Update domain URN with URN prefix and island name
            # (warning: problem when changing the following var)
            self.domain_urn = domain_name
            db_peers = {}
            for peer in peers:
                db_peer = db_sync_manager.get_configured_peer_by_urn(peer)
                # Looks for referred domain through peer ID;
                # retrieve URN and last update
                filter_params = {"_ref_peer": db_peer.get("_id")}
                # For the MRO environment, it is possible to have
                # multiple domains in the same island
                db_peers[peer] = {
                    "db_peer": db_peer,
                    "domain_urns": set(),
                    "domain_last_update": None
                }
                for domain_peer in db_sync_manager.\
                        get_domains_info(filter_params):
                    try:
                        domain_peer_urn = domain_peer.get("domain_urn")
                        physical_topology = db_sync_manager.\
                            get_physical_info_from_domain(
                                domain_peer.get("_id"))
                        domain_last_update = physical_topology.\
                            get("last_update")
                        db_peers[peer]["domain_urns"].add(domain_peer_urn)
                        db_peers[peer]["domain_last_update"] = \
                            domain_last_update

                        self.domain_peer_urn = domain_peer_urn
                        # Choose less recent time of last update
                        if not self.domain_last_update:
                            if domain_last_update < self.domain_last_update:
                                self.domain_last_update = domain_last_update
                    except Exception as e:
                        logger.warning("Physical topology - Cannot recover \
                        information for peer='%s'. Skipping to the next \
                        peer. Details: %s" % (peer, e))
                        logger.warning(traceback.format_exc())
            # Add general information to the topology
            self.__add_general_info()

            # For a MRO environment, we need to send single
            # copy of the same information
            domain_urn_set = set()
            for v in db_peers.values():
                domain_urn_set.update(v.get("domain_urns"))

            for durn in domain_urn_set:
                # Retrieve proper resources
                self.retrieve_topology_by_peer(durn)
        except Exception as e:
            logger.warning("Physical topology - Cannot recover information \
            for domain='%s'. Skipping to the next domain. \
            Details: %s" % (domain_name, e))
            logger.warning(traceback.format_exc())

    def __get_island_name(self, urn):
        return URNUtils.get_felix_authority_from_urn(urn)

    def __get_topology_ref(self, topolist, name, uptime, typee):
        for topo in topolist.iter("topology"):
            # Match must be exact (use delimiters to force)
            if topo.get("name").endswith(":" + name):
                return topo
        # Create a new topology tag
        if len(name) > 0:
            return etree.SubElement(
                topolist, "topology",
                attrib={"last_update_time": uptime,
                        "type": typee,
                        "name": "urn:publicid:IDN+ocf:" + name})

    def __add_tn_node_per_island(self, topo_list, node):
        for topo in topo_list.iter("topology"):
            topo.append(deepcopy(node))

    def __cycle_nodes(self, topo, tmp_topo):
        for node in topo.iter("node"):
            if node.get("type") == "tn":
                self.__add_tn_node_per_island(tmp_topo, node)
                return True
        return False

    def __group_resources_per_island(self):
        tmp_topology_list = etree.Element("topology_list")
        for topology in self.topology_list.iter("topology"):
            # Nodes
            for node in topology.iter("node"):
                island = self.__get_island_name(node.get("id"))
                toporef = self.__get_topology_ref(
                    tmp_topology_list, island,
                    topology.get("last_update_time"),
                    topology.get("type"))
                # do not copy TN nodes here
                if node.get("type") != "tn":
                    toporef.append(deepcopy(node))
            # Links
            for link in topology.iter("link"):
                island = self.__get_island_name(link.get("id"))
                toporef = self.__get_topology_ref(
                    tmp_topology_list, island,
                    topology.get("last_update_time"),
                    topology.get("type"))
                toporef.append(deepcopy(link))
        # MMS waits for 1 TN node per island
        for topology in self.topology_list.iter("topology"):
            if self.__cycle_nodes(topology, tmp_topology_list):
                break
        # Save the current topology list in the base class
        self.set_topology_tree(tmp_topology_list)
