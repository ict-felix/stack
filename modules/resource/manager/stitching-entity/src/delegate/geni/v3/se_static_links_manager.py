from delegate.geni.v3.db_manager_se import db_sync_manager
import core
import se_configurator as SEConfigurator

logger = core.log.getLogger("se-static-link-manager")

class StaticLinkVlanManager(object):
    """This object is for static links VLAN management"""

    def __init__(self):
        # TODO: change this to minimise the query result size
        self.getVlansForPorts = db_sync_manager.get_resources()
        self.vlansForStaticLinks = {}
        self.SEResources = SEConfigurator.seConfigurator()

    def getVlanForInterface(self, urn):
        return self.vlansForStaticLinks[urn]

    def getVlanMapping(self):
        return self.vlansForStaticLinks

    def chooseVlan(self, port): # TODO: add VLAN choosing   .keys()[0]
        # get available VLANs for the static link
        vlans = self.SEResources.get_concrete_port_status(port)
        # choose the first avaialble VLAN
        for vlan in vlans:
            if vlans[vlan] == True:
                logger.info("Port %s: Choosing VLAN %s for static link" %(port, vlan))
                self.vlansForStaticLinks[port] = vlan
                return vlan
        # vlansPorts = self.getVlansForPorts
        # for vlan in vlansPorts[port]:
        #     if vlansPorts[port][vlan] == True:
        #         logger.info("VLAN %s for static link on port %s has been choosed." %(vlan, port))
        #         self.vlansForStaticLinks[port] = vlan
        #         return vlan



#### TODO:  - add getting first/n available Vlans
####        - extracting port from component_id urn