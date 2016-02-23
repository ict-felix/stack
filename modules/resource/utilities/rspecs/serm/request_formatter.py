from core.utils.urns import URNUtils
from rspecs.tnrm.request_formatter import DEFAULT_XS,\
    TNRMv3RequestFormatter, DEFAULT_XMLNS, DEFAULT_SHARED_VLAN,\
    DEFAULT_REQ_SCHEMA_LOCATION
from lxml import etree

DEFAULT_FELIX = "http://ict-felix.eu/serm_request"


class SERMv3RequestFormatter(TNRMv3RequestFormatter):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        super(SERMv3RequestFormatter, self).__init__(
            xmlns, xs, sharedvlan, DEFAULT_FELIX, schema_location)
        self.__sv = sharedvlan

    def node(self, n, sharedvlan_ns_in_ifaces=True):
        """
        Same logic as in TNRM, but with ability to avoid including
        'sharedvlan' namespace for RSPecs with new format
        """
        node_ = etree.SubElement(self.rspec, "{%s}node" % (self.xmlns))
        node_.attrib["client_id"] = n.get("component_id")
        node_.attrib["component_manager_id"] = n.get("component_manager_id")

        if n.get("exclusive") is not None:
            node_.attrib["exclusive"] = n.get("exclusive")

        if n.get("sliver_type_name") is not None:
            sliver_ = etree.SubElement(node_, "{%s}sliver_type" % (self.xmlns))
            sliver_.attrib["name"] = n.get("sliver_type_name")

        for i in n.get("interfaces"):
            intf_ = etree.SubElement(node_, "{%s}interface" % (self.xmlns))
            intf_.attrib["client_id"] = i.get("component_id")

            if sharedvlan_ns_in_ifaces:
                for v in i.get("vlan"):
                    svlan_ = etree.SubElement(intf_,
                                              "{%s}link_shared_vlan" % (self.__sv))
                    svlan_.attrib["vlantag"] = v.get("tag")
                    if v.get("name") is not None:
                        svlan_.attrib["name"] = v.get("name")
                    if v.get("description") is not None:
                        svlan_.attrib["description"] = v.get("description")

    def link(self, link):
        l = etree.SubElement(self.rspec, "{%s}link" % (self.xmlns))
        link_cid = link.get("component_id")
        l.attrib["client_id"] = link_cid

        if link.get("component_manager_name") is not None:
            m = etree.SubElement(l, "{%s}component_manager" % (self.xmlns))
            m.attrib["name"] = link.get("component_manager_name")

        t = etree.SubElement(l, "{%s}link_type" % (self.xmlns))
        t.attrib["name"] = link.get("link_type")

        for i in link.get("interface_ref"):
            interface = etree.SubElement(l, "{%s}interface_ref" % (self.xmlns))
            if_cid = i.get("component_id")

            # NOTE: commented due to failure on internal DB retrieval
            # New RSpec style (including VLANs in link) =>
            # add "+vlan=<VLAN>" to the comp. ID of each interface
            # if_cid = add_vlan_to_link(link_cid, iface_cid)
            interface.attrib["client_id"] = if_cid

            # Note: vlantag attribute used only in original RSpec format
            # (where VLANs are not defined in the interface's component ID)
            if "vlan=" not in i.get("component_id") and \
                    i.get('vlantag') is not None:
                interface.attrib["{%s}vlan" % (DEFAULT_FELIX)] =\
                    i.get('vlantag')

        # NOTE: property tag not used
        # for p in link.get("property"):
        #     prop = etree.SubElement(l, "{%s}property" % (self.xmlns))
        #     prop.attrib["source_id"] = p.get("source_id")
        #     prop.attrib["dest_id"] = p.get("dest_id")
        #     prop.attrib["capacity"] = p.get("capacity")

    def add_vlan_to_link(self, link_cid, iface_cid):
        """
        Add vlan to component ID of link's interface
        when using a newly formatted RSpec.
        This format is used: "urn+...+datapath+<dpid>_<port>+vlan=<vlan>.
        """
        if "vlan=" in link_cid:
            urn_src, vlan_src, urn_dst, vlan_dst = \
                URNUtils.get_fields_from_domain_link_id(link_cid)
            if_vlan_pairs = {urn_src: vlan_src, urn_dst: vlan_dst}
            # if_dpid = URNUtils.get_datapath_from_datapath_id(if_cid)
            if_dpid, if_port = \
                URNUtils.get_datapath_and_port_from_datapath_id(iface_cid)
            if_dpid_port = "%s_%s" % (if_dpid, if_port)
            for if_vlan in if_vlan_pairs.keys():
                if if_dpid_port in if_vlan:
                    iface_cid += "+vlan=%s" % if_vlan_pairs[if_vlan]
                    break
        return iface_cid
