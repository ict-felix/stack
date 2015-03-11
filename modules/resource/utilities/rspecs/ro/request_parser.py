from rspecs.parser_base import ParserBase
from rspecs.crm.request_parser import CRMv3RequestParser
from rspecs.openflow.request_parser import OFv3RequestParser
from rspecs.tnrm.request_parser import TNRMv3RequestParser


class RORequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(RORequestParser, self).__init__(from_file, from_string)
        self.__com_parser = CRMv3RequestParser(from_file, from_string)
        self.__of_parser = OFv3RequestParser(from_file, from_string)
        self.__tn_parser = TNRMv3RequestParser(from_file, from_string)

    # COM resources
    def com_nodes(self):
        try:
            return self.__com_parser.get_nodes()
        except:
            return []

    def com_slivers(self):
        try:
            return self.__com_parser.get_slivers()
        except:
            return []

    # OF resources
    def of_sliver(self):
        try:
            return self.__of_parser.get_sliver(self.rspec)
        except:
            return None

    def of_controllers(self):
        return self.__of_parser.get_controllers(self.rspec)

    def of_groups(self):
        return self.__of_parser.get_groups(self.rspec)

    def of_matches(self):
        return self.__of_parser.get_matches(self.rspec)

    # TN resources
    def tn_nodes(self):
        try:
            return self.__tn_parser.get_nodes(self.rspec)
        except:
            return []

    def tn_links(self):
        try:
            return self.__tn_parser.get_links(self.rspec)
        except:
            return []