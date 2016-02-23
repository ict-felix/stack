from core.utils.urns import URNUtils
from rspecs.parser_base import ParserBase
from rspecs.commons_se import SELink
from rspecs.commons_tn import Node, Interface

import core
logger = core.log.getLogger("utility-rspec")


class SERMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3RequestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')
        self.__felix = self.rspec.nsmap.get('felix')
        self.__proto = self.rspec.nsmap.get('protogeni')

    def check_se_node_resource(self, node):
        # according to the proposed URNs structure, a SE-node MUST have
        # "serm" as resource-name (client_id) and authority
        # (component_manager_id) fields
        # At least we verify the autority field here!
        if node.attrib.get("component_manager_id", None) is not None and \
                node.attrib.get("client_id", None) is not None:
            if "serm" in node.attrib.get("component_manager_id", "") or \
                    "serm" in node.attrib.get("client_id", ""):
                return True
        return False

    def check_se_link_resource(self, link, c_manager):
        # according to the proposed URNs structure, a TN-link MUST have
        # "serm" as resource-name (client_id) and authority
        # (component_manager_name) fields
        # At least we verify the autority field here!
        if not c_manager.attrib.get("name"):
            return False
        if "serm" in c_manager.attrib.get("name"):
            return True
        return False

    def update_protogeni_cm_uuid(self, tag, obj):
        cmuuid = tag.attrib.get("{%s}component_manager_uuid" % (self.__proto))
        if cmuuid is not None:
            obj.add_component_manager_uuid(cmuuid)

    def get_nodes(self, rspec):
        nodes = []
        for n in rspec.findall(".//{%s}node" % (self.none)):
            if not self.check_se_node_resource(n):
                logger.info("Skipping this node, not a SE-res: %s", (n,))
                continue

            node = Node(n.attrib.get("client_id"),
                        n.attrib.get("component_manager_id"),
                        n.attrib.get("exclusive"))

            self.update_protogeni_cm_uuid(n, node)

            for i in n.iterfind("{%s}interface" % (self.none)):
                interface = Interface(i.attrib.get("client_id"))
                # Note: old format using 'sharedvlan' namespace
                for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                    interface.add_vlan(sv.attrib.get("vlantag"),
                                       sv.attrib.get("name"))
                node.add_interface(interface.serialize())

            nodes.append(node.serialize())
        return nodes

    def nodes(self):
        return self.get_nodes(self.rspec)

    def get_links(self, rspec):
        links_ = []

        for l in rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))

            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            if not self.check_se_link_resource(l, manager_):
                logger.info("Skipping this link, not a SE-res: %s", (l,))
                continue

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            # Note: client_id for a link may follow one of the formats:
                # Original: "urn:publicid:IDN+fms:psnc:serm+link+
                # <dpid1>_6_<dpid2>_7",
                # New: "urn:publicid:IDN+fms:psnc:serm+link+
                # <dpid1>_6?vlan=1_<dpid2>_7?vlan=2",
            # In case of receiving the new one, it must be translated to
            # the original one (advertised by SERM); otherwise it will not be
            # possible to find the link in the Mongo serm.link collection
            client_id = l.attrib.get("client_id")
            # client_id_2 = URNUtils.convert_se_link_id_to_adv_id(client_id)

            l_ = SELink(client_id, type_.attrib.get("name"),
                        manager_.attrib.get("name"))
            self.update_protogeni_cm_uuid(l, l_)

            # FIXME: VLAN seems not properly added to interface
            for i in l.iterfind("{%s}interface_ref" % (self.none)):
                # 1st check new SERM RSpec format
                client_id, vlan = URNUtils.\
                    get_fields_from_domain_iface_id(i.attrib.get("client_id"))
                if not vlan:
                    vlan = i.attrib.get("{%s}vlan" % (self.__felix))

                l_.add_interface_ref(client_id, vlan)

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_

    def links(self):
        return self.get_links(self.rspec)
