import core

logger = core.log.getLogger("monitoring-utils")


class MonitoringUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def check_existing_tag_in_topology(root, node, node_type, node_urns,
                                       domain=None):
        tag_exists = False
        try:
            elements = []
            if not isinstance(node_urns, list):
                node_urns = [node_urns]
            try:
                for node_urn in node_urns:
                    if node == "link":
                        elements.extend(
                            MonitoringUtils.
                            check_existing_link_tag_in_topology(
                                root, node_type, node_urn))
                    else:
                        node_elements = MonitoringUtils.\
                            check_existing_generic_tag_in_topology(
                                root, node, node_type, node_urn, domain)
                        if len(node_elements) > 0:
                            elements = node_elements
            except:
                pass
            if len(elements) > 0:
                tag_exists = True
        except:
            pass
        return tag_exists

    @staticmethod
    def check_existing_generic_tag_in_topology(root, node, node_type, node_urn,
                                               domain=None):
        elements = []
        if node_type == "tn":
            if domain is not None:
                domain = domain if "urn" in domain else \
                    "urn:publicid:IDN+ocf:" + domain
                if node_type is None:
                    elements = root.xpath(
                        "//topology[@name='%s']//%s[@id='%s']" %
                        (domain, node, node_urn))
                elements = root.xpath(
                    "//topology[@name='%s']//%s[@type='%s'][@id='%s']" %
                    (domain, node, node_type, node_urn))
        else:
            elements = root.xpath(
                "//%s[@type='%s'][@id='%s']" %
                (node, node_type, node_urn))
            if node_type is None:
                elements = root.xpath("//%s[@id='%s']" % (node, node_urn))
        return elements

    @staticmethod
    def check_existing_link_tag_in_topology(root, node_type, node_urn):
        elements = []
        interfaces_same_link = True
        elem = root.xpath(
            "//link[@type='%s']//interface_ref[@client_id='%s']" %
            (node_type, node_urn))
        if node_type is None:
            elem = root.xpath(
                "//link//interface_ref[@client_id='%s']" % node_urn)
        for element in elements:
            if element.getparent() == elem[0].getparent():
                interfaces_same_link &= True
            else:
                interfaces_same_link &= False
        if interfaces_same_link:
            elements.extend(elem)
        return elements

    @staticmethod
    def find_virtual_link_end_to_end(hybrid_links):
        # Retrieve the endpoints of the slice ("abstract link" in M/MS)
        e2e_link_urns = set()
        # 1) Check for SDNRM-SDNRM end-paths
        for se_link in hybrid_links:
            # 1) Check for SDN-SDN end paths
            # 2) Check for SDN-TN end paths
            for link_end in [":ofam", ":tnrm"]:
                if link_end in se_link["source"]:
                    e2e_link_urns.add(se_link["source"])
                if link_end in se_link["destination"]:
                    e2e_link_urns.add(se_link["destination"])
        return list(e2e_link_urns)

    @staticmethod
    def find_virtual_links(topology_root):
        links_ids = []
        for link_id in topology_root.xpath("//topology//link[@id]"):
            links_ids.append(link_id.attrib["id"])
        return links_ids

    @staticmethod
    def find_slice_name(topology_root):
        slice_name = ""
        try:
            slice_name = topology_root.xpath("//topology")[0].attrib["name"]
        except Exception as e:
            logger.warning("Unable to retrieve slice name for topology. \
                            Details: %s" % e)
        return slice_name
