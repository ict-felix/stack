from core.utils.urns import URNUtils


class PathFinderTNtoSDNOrganisationUtils(object):

    organisation_name_mappings = {
        "psnc": ["pionier"],
        "iminds": ["iMinds"],
        "kddi": ["jgn-x.jp"],
    }

    @staticmethod
    def get_authority(urn):
        return URNUtils.get_felix_authority_from_urn(urn)

    @staticmethod
    def get_authority_from_tn(urn):
        if ":ogf:" in urn:
            hrn = urn.split(":")[3]
            # HRN samples: i2cat.net, aist.go.jp, pionier.net.pl
            urn = hrn.split(".")[0]
        return urn

    @staticmethod
    def get_exact_org(organisation_name):
        return ":%s:" % organisation_name

    @staticmethod
    def get_organisation_mappings(organisation_name):
        # Return possible alternatives, given an organisation name
        return PathFinderTNtoSDNOrganisationUtils.\
            organisation_name_mappings.get(
                organisation_name, [organisation_name])

    @staticmethod
    def check_auth_alt_se_in_mappings(se_link_interfaces):
        """
        Given a link between SE and other interface, find out
        if both interfaces are managed exactly by the same authority
        > This controls cases where multiple sites are offered
        under the same authority under TN (but different in SE and SDN)
        """
        se_tn_same_auth = False
        se_auth = PathFinderTNtoSDNOrganisationUtils.\
            get_authority(se_link_interfaces[0])
        se_auth_alt = se_auth
        tn_auth = PathFinderTNtoSDNOrganisationUtils.\
            get_authority_from_tn(se_link_interfaces[1])
        auth_alt_mappings = PathFinderTNtoSDNOrganisationUtils.\
            get_organisation_mappings(se_auth)
        for au in auth_alt_mappings:
            if tn_auth == au.split(".")[0]:
                se_tn_same_auth = True
                break
        return se_tn_same_auth
