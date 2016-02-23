from core.organisations import AllowedOrganisations as AllowedOrgs
from core.utils.strings import StringUtils
# from extensions.sfa.util.xrn import get_authority
from extensions.sfa.util.xrn import urn_to_hrn


class URNUtils:
    """
    Contains common operations related to URN processing.
    """
    # Dictionaries
    FELIX_ORGS = AllowedOrgs.get_organisations_type()
    FELIX_ORGS_ALIAS = AllowedOrgs.get_organisations_type_with_alias()

#    @staticmethod
#    def get_authority_from_urn(urn):
#        hrn, hrn_type = urn_to_hrn(urn)
#        # Remove leaf (the component_manager part)
#        hrn_list = hrn.split(".")
#        hrn = ".".join(hrn_list[:-1])
#        authority = get_authority(hrn)
#        return authority

    @staticmethod
    def get_authority_from_urn(urn):
        authority = ""
        try:
            urn_delimiters = StringUtils.find_all(urn, "+")
            idx1 = urn_delimiters[0]
            idx2 = urn_delimiters[1]
            full_auth = urn[idx1+1:idx2]
            auth_components = full_auth.split(":")
            authority = auth_components[1]
            orgs = map(lambda x: x in authority, URNUtils.FELIX_ORGS)
            authority = URNUtils.FELIX_ORGS[orgs.index(True)]
        except:
            pass
        return authority

    @staticmethod
    # Expects URN of "authority" type, not any URN
    #  e.g. urn:publicid:IDN+openflow:ocf:i2cat:vtam+authority+cm
    def get_felix_authority_from_urn(urn):
        authority = ""
        hrn, hrn_type = urn_to_hrn(urn)
        # Remove leaf (the component_manager part)
        hrn_list = hrn.split(".")
        hrn = ".".join(hrn_list[:-1])
        for hrn_element in hrn_list:
            if hrn_element in URNUtils.FELIX_ORGS:
                authority = hrn_element
                break
        # URN may not follow the standard format...
        if len(authority) == 0:
            try:
                URNUtils.get_authority_from_urn(urn)
            except:
                pass
        return authority

    @staticmethod
    # Expects URN of OGF "authority" type
    #   e.g. urn:ogf:network:i2cat.net:2015:gre:felix
    def get_felix_authority_from_ogf_urn(urn):
        authority = ""
        ogf_prefix = "urn:ogf:network:"
        ogf_idx = urn.find(ogf_prefix)
        if ogf_idx >= 0:
            urn = urn[ogf_idx:]
        auth = urn.replace(ogf_prefix, "")
        hrn_list = auth.split(":")
        for org in URNUtils.FELIX_ORGS_ALIAS:
            for hrn_element in hrn_list:
                if org in hrn_element:
                    authority = AllowedOrgs.find_organisation_by_alias(org)
                break
        # URN may not follow the standard format...
        if len(authority) == 0:
            try:
                URNUtils.get_authority_from_urn(urn)
            except:
                pass
        return authority

    @staticmethod
    # Expects URN of SERM/TNRM link
    def get_fields_from_domain_link_id(link_id):
        urn_src, vlan_src, urn_dst, vlan_dst = "", "", "", ""
        import re
        try:
            # TN format
            try:
                urn_reg = \
                    "urn.*(urn.*)\?vlan=(\d{1,4})-(urn.*)\?vlan=(\d{1,4})+.*"
                groups_reg = re.match(urn_reg, link_id)
                # Force exception check
                groups_reg.group(0)
            # SE format
            except:
                urn_reg = "urn(.*)\?vlan=(\d{1,4})-(.*)\?vlan=(\d{1,4})"
                groups_reg = re.match(urn_reg, link_id)
            urn_src, vlan_src, urn_dst, vlan_dst = \
                [groups_reg.group(i) for i in xrange(1, 5)]
            urn_src = "urn" + urn_src
        except:
            pass
        return urn_src, vlan_src, urn_dst, vlan_dst

    @staticmethod
    # Expects URN of SERM link
    def convert_se_link_id_to_adv_id(link_id):
        """
        Removes VLANs from the SE link so it is possible to search in DB.
        """
        urn_src, _, urn_dst, _ = \
            URNUtils.get_fields_from_domain_link_id(link_id)
        return "%s_%s" % (urn_src, urn_dst)

    @staticmethod
    # Expects URN of SERM/TNRM interface
    def get_fields_from_domain_iface_id(iface_id):
        """
        In case of failure, return the interface ID as 1st parameter
        (because VLAN may be not present in original format for RSpecs)
        """
        urn, vlan = iface_id, ""
        import re
        try:
            urn_reg = "urn(.*)\+vlan=(\d{1,4})"
            groups_reg = re.match(urn_reg, iface_id)
            urn, vlan = [groups_reg.group(i) for i in xrange(1, 3)]
            urn = "urn" + urn
        except:
            pass
        return urn, vlan

    @staticmethod
    # Expects URN of SDNRM/SERM datapath or some partial link
    def get_datapath_from_datapath_id(link_id):
        datapath = ""
        try:
            import re
            # Note: typically this would use 'datapath', but can make
            # use of greedy evaluation to fetch all groups till the end
            urn_reg = "urn(.*)\+(.*)_\d+"
            groups_reg = re.match(urn_reg, link_id)
            _, datapath = [groups_reg.group(i) for i in xrange(1, 3)]
        except:
            pass
        return datapath

    @staticmethod
    # Expects URN of SDNRM/SERM datapath or some partial link
    def get_datapath_and_port_from_datapath_id(link_id):
        datapath = ""
        try:
            import re
            urn_reg = "urn(.*)\+(.*)_(\d+)"
            groups_reg = re.match(urn_reg, link_id)
            _, datapath, port = [groups_reg.group(i) for i in xrange(1, 4)]
        except:
            pass
        return datapath, port
