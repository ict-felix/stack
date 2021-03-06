from mapper.utils.format import PathFinderTNtoSDNFormatUtils as FormatUtils
from mapper.utils.org import PathFinderTNtoSDNOrganisationUtils as OrgUtils

class PathFinderTNtoSDNFilterUtils(object):

    @staticmethod
    def find_sdn_interfaces_for_se_interface(se_links, se_interface, negative_filter=[], possitive_filter=[""]):
        sdn_interfaces_match = set()
        for se_link in se_links:
            se_link_interfaces = [ iface.get("component_id") for iface in se_link.get("interface_ref") ]
            se_link_interfaces_match = any([ FormatUtils.remove_port_cid(se_interface) in se_link_interface for se_link_interface in se_link_interfaces ])
            if se_link_interfaces_match:
                # Retrieve link interfaces from SDN switches that are connected with any SE interface
                # Search for some SDN link connected to the passed SE component id (without port!)
                se_interface_noport = FormatUtils.remove_port_cid(se_interface)
                # Also, avoid adding links SE-TN (this would introduce a never-ending loop)
                if se_interface_noport in se_link_interfaces[0] \
                        and not any([ param in se_link_interfaces[1] for param in negative_filter ]) \
                        and any([ param in se_link_interfaces[1] for param in possitive_filter ]):
                    sdn_interfaces_match.add(se_link_interfaces[1])
                elif se_interface_noport in se_link_interfaces[1] \
                        and not any([ param in se_link_interfaces[0] for param in negative_filter ]) \
                        and any([ param in se_link_interfaces[0] for param in possitive_filter ]):
                    sdn_interfaces_match.add(se_link_interfaces[0])
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(sdn_interfaces_match)

    @staticmethod
    def find_se_interfaces_for_domain_names(se_links, mappings, src_domain, dst_domain):
        se_interfaces_matches = set()
        for se_link in se_links:
            #if tn_interface in se_link.get("component_id"):
            se_link_interfaces = [ FormatUtils.clean_tn_stp_cid(iface.get("component_id")) for iface in se_link.get("interface_ref") ]
            # Both source and destination must exist in an SE-SE link
            src_alias = [ src_domain ]
            src_alias.extend([ dom for dom in OrgUtils.get_organisation_mappings(src_domain) ])
            # Looking for matches in src and dst domains. Using ":" as delimiter
            src_alias_match = any([ ":"+alias+":" in iface for alias in src_alias for iface in se_link_interfaces ])
            dst_alias = [ dst_domain ]
            dst_alias.extend([ dom for dom in OrgUtils.get_organisation_mappings(dst_domain) ])
            dst_alias_match = any([ ":"+alias+":" in iface for alias in dst_alias for iface in se_link_interfaces ])
            if src_alias_match and dst_alias_match:
                se_link_interfaces = [ FormatUtils.clean_tn_stp_cid(iface.get("component_id")) for iface in se_link.get("interface_ref") ]
                candidate_set = (se_link_interfaces[0], se_link_interfaces[1])
                if not set(candidate_set).issubset(se_interfaces_matches):
                    se_interfaces_matches.add(tuple(candidate_set))
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(se_interfaces_matches)

    @staticmethod
    def find_se_sdn_links_for_se_node(se_links, se_node, negative_filter=[], possitive_filter=[""]):
        sdn_se_links = set()
        for se_link in se_links:
            se_link_interfaces = [ iface.get("component_id") for iface in se_link.get("interface_ref") ]
            se_link_interfaces_match = any([ se_node in se_link_interface for se_link_interface in se_link_interfaces ])
            if se_link_interfaces_match:
                # Retrieve link interfaces from SDN switches that are connected with any SE interface
                # Search for some SDN link connected to the passed SE component id (without port!)
                se_interface_noport = se_node
                # Also, avoid adding links SE-SE and SE-TN (this would introduce a never-ending loop)
                if se_interface_noport in " ".join(se_link_interfaces[:]) and \
                        any([ "ofam" in link for link in se_link_interfaces]) and \
                        not any([ param in " ".join(se_link_interfaces[:]) for param in negative_filter ]) and \
                        any([ param in " ".join(se_link_interfaces[:]) for param in possitive_filter ]):
                    sdn_se_links.add(tuple(se_link_interfaces))
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(sdn_se_links)

    @staticmethod
    def find_se_interfaces_for_tn_interface(se_links, tn_interface):
        se_interfaces_match = set()
        for se_link in se_links:
            #if tn_interface in se_link.get("component_id"):
            se_link_interfaces = [ FormatUtils.clean_tn_stp_cid(iface.get("component_id")) for iface in se_link.get("interface_ref") ]
            # Checks:
            # 1. TN interface is connected to some SE interface
            # 2. Same authority for both (e.g. control AIST/AIST2 DC case)
            if tn_interface in se_link_interfaces \
                    and OrgUtils.check_auth_alt_se_in_mappings(se_link_interfaces):
                se_link_interfaces = [ FormatUtils.clean_tn_stp_cid(iface.get("component_id")) for iface in se_link.get("interface_ref") ]
                # Remove link interface that matches with the passed TN interface
                se_link_interfaces.pop(se_link_interfaces.index(tn_interface))
                se_interfaces_match.add(se_link_interfaces[0])
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(se_interfaces_match)

    @staticmethod
    def find_tn_interfaces_for_domain(tn_interfaces_cids, domain_names_alt, domain_name):
        # Given a domain name (e.g. "kddi", "aist"), find possible TN interfaces
        domain_name_alt_matches = set()    
        # A set is used to add possible TN interfaces. This avoids duplications
        for domain_name_alt in domain_names_alt:
            domain_name_alt_matches.add(tuple(s for s in tn_interfaces_cids if domain_name_alt in s))
        return domain_name_alt_matches

    @staticmethod
    def filter_tn_interfaces_by_type(tn_interfaces_cids, link_type=""):
        # Given a link type (e.g. "nsi" or "gre"), filter possible TN interfaces
        if link_type.lower() == "gre":
            tn_interfaces_cids = filter(lambda x: "gre" in x, tn_interfaces_cids)
        # "Se non e vaca, e boi"
        elif link_type.lower() == "nsi":
            tn_interfaces_cids = filter(lambda x: "gre" not in x, tn_interfaces_cids)
        return tn_interfaces_cids

    @staticmethod
    def ensure_same_type_tn_interfaces(tn_interfaces):
        """
        Verify that, for a given list of STPs, all of them
        are of the same type (either using NSI or GRE).
        """
        tn_interface_type = None
        for i, tn_interface in enumerate(tn_interfaces):
            if tn_interface_type is None:
                if "gre" in tn_interface:
                    tn_interface_type = "gre"
                else:
                    tn_interface_type = "nsi"
            else:
                if (tn_interface_type == "gre" and ":"+tn_interface_type+":" not in tn_interface) or \
                (tn_interface_type == "nsi" and ":gre:" in tn_interface):
                    del(tn_interfaces[i])
        return tn_interfaces

    @staticmethod
    def get_se_interfaces_cid_from_link(se_link, clean=False):
        # Return a list with a set of two component_id values for the given SE link
        interfaces = se_link.get("interface_ref", {})
        processed_interfaces = []
        for interface in interfaces:
            processed_interface = interface.get("component_id", "")
            if clean == True:
                # Some of the SE links are SE-TN links
                processed_interface = FormatUtils.clean_tn_stp_cid(processed_interface)
            processed_interfaces.append(processed_interface)
        return list(set(processed_interfaces))

    @staticmethod
    def check_path_with_src_and_dest(mapping_path_element):
        if all( [ len(mapping_path_element["src"][elem]) > 0 for elem in mapping_path_element["src"] ]) \
            and all( [ len(mapping_path_element["dst"][elem]) > 0 for elem in mapping_path_element["dst"] ]):
            return True
        return False

    @staticmethod
    def check_path_with_different_stps(mapping_path_element):
        tn_src = mapping_path_element["src"].get("tn", None)
        tn_dst = mapping_path_element["dst"].get("tn", None)
        # TN endpoints must be different and have the same type
        if tn_src is not None and tn_dst is not None and tn_src != tn_dst:
            return True
        return False

    @staticmethod
    def check_path_with_same_type_stps(mapping_path_element):
        tn_src = mapping_path_element["src"].get("tn", None)
        tn_dst = mapping_path_element["dst"].get("tn", None)
        tn_interfaces = PathFinderTNtoSDNFilterUtils.ensure_same_type_tn_interfaces([tn_src, tn_dst])
        if len(tn_interfaces) == 2:
            return True
        return False

    @staticmethod
    def prune_unlinked_dpids(mapping_path_structure, dpids_src_list, dpids_dst_list, check_by_auth=False):
        """
        Prunes those paths that do not conform to the passed SRC and DST DPID list.
        That is, the resulting paths must contain at least all the required SRC and DST DPIDs.

        @param check_by_auth when True, checks if the path contains a DPID with the required authority
                             when False, looks for exact DPIDs on the path
        """
        new_mapping_path_structure = []
        for idx, mapping_path_element in enumerate(mapping_path_structure):
            # Source sets
            src_dpids_avail = set([ x["sdn"] for x in mapping_path_element["src"]["links"] ])
            # Destination sets
            dst_dpids_avail = set([ x["sdn"] for x in mapping_path_element["dst"]["links"] ])
            if check_by_auth:
                src_dpids_auth_avail = set(OrgUtils.get_authority(x) for x in src_dpids_avail)
                src_dpids_auth_req = set(OrgUtils.get_authority(x) for x in dpids_src_list)
                dst_dpids_auth_avail = set(OrgUtils.get_authority(x) for x in dst_dpids_avail)
                dst_dpids_auth_req = set(OrgUtils.get_authority(x) for x in dpids_dst_list)
                src_dpids_auth_match = src_dpids_auth_avail.intersection(src_dpids_auth_req)
                dst_dpids_auth_match = dst_dpids_auth_avail.intersection(dst_dpids_auth_req)
                # Loose check -> the authorities of the requested DPIDs must match
                full_match = len(src_dpids_auth_match) == len(src_dpids_auth_req) and len(dst_dpids_auth_match) == len(dst_dpids_auth_req)
            else:
                src_dpids_match = src_dpids_avail.intersection(dpids_src_list)
                dst_dpids_match = dst_dpids_avail.intersection(dpids_dst_list)
                # Tight check -> all requested DPIDs must be present (i.e. intersected with the available DPIDs)
                full_match = len(src_dpids_match) == len(dpids_src_list) and len(dst_dpids_match) == len(dpids_dst_list)
            if full_match:
                new_mapping_path_structure.append(mapping_path_element)
        return new_mapping_path_structure

    @staticmethod
    def prune_invalid_paths(mapping_path_structure):
        new_mapping_path_structure = []
        # There must be information in SRC and DST links
        ## Check all keys (SRC, DST) inside the "mapping_path_structure" list
        if not all([ all(len(val) > 0 for val in elem.values()) for elem in mapping_path_structure ]):
            return new_mapping_path_structure
        # There must also be information for links (SRC+DST), and...
        for idx, mapping_path_element in enumerate(mapping_path_structure):
            if PathFinderTNtoSDNFilterUtils.check_path_with_src_and_dest(mapping_path_element):
                # TN endpoints must be different and have the same type
                if PathFinderTNtoSDNFilterUtils.check_path_with_different_stps(mapping_path_element) \
                    and PathFinderTNtoSDNFilterUtils.check_path_with_same_type_stps(mapping_path_element):
                    new_mapping_path_structure.append(mapping_path_element)
        return new_mapping_path_structure
