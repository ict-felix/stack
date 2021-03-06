from delegate.geni.v3.rspecs.serm.request_parser import SERMv3RequestParser
from delegate.geni.v3.rspecs.commons_se import SELink


class SERMv3ManifestParser(SERMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3ManifestParser, self).__init__(from_file, from_string)

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
                        manager_.attrib.get("name"), l.attrib.get("vlantag"),
                        l.attrib.get("sliver_id"))

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_
