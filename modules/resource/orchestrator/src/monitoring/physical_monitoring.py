from db.db_manager import db_sync_manager
from monitoring.base_monitoring import BaseMonitoring

import core
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-physical")


class PhysicalMonitoring(BaseMonitoring):
    """
    Periodically communicates physical topology to the MS.
    """

    def __init__(self):
        super(PhysicalMonitoring, self).__init__()

    def retrieve_topology(self, peer):
        # General information
        self.__add_general_info()
        # COM resources
        self._add_com_info()
        # SDN resources
        self._add_sdn_info()
        # TN resources
        self._add_tn_info()
        # SE resources
        self._add_se_info()

    def send_topology(self, monitoring_server):
        logger.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            try:
                # Looks for referred domain through peer ID; retrieve URN and last update
                filter_params = {"_ref_peer": peer.get("_id"),}
                domain_peer = db_sync_manager.get_domain_info(filter_params)
                self.domain_peer_urn = domain_peer.get("domain_urn")

                physical_topology = db_sync_manager.get_physical_info_from_domain(domain_peer.get("_id"))
                self.domain_last_update = physical_topology.get("last_update")
                logger.debug("Peer=%s, domain=%s" % (peer, self.domain_peer_urn,))
            
                # Retrieve topology per peer
                self.retrieve_topology(peer)

                # Check: remove any 'topology' without contents
                self._remove_empty_topologies(self.domain_peer_urn, self.domain_last_update)
            except Exception as e:
                logger.warning("Physical topology - Cannot recover information for peer (id='%s'). Skipping to the next peer" % peer.get("_id"))

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
        topo = ET.SubElement(self.topology_list, "topology")
        # Milliseconds in UTC format
        topo.attrib["last_update_time"] = self.domain_last_update
        topo.attrib["type"] = "physical"
        topo.attrib["name"] = self.domain_urn
        # Set topology tag as root node for subsequent operations
        self.topology = topo
