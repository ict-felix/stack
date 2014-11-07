DEFAULT_COM = "http://www.geni.net/resources/rspec/3"


# COM Data Models
class Node(object):
    # Node unavailable unless the contrary is said
    def __init__(self, component_id, component_name, component_manager_id, 
                 exclusive=None, available=False, interfaces=[]):
        self.node = {"component_id": component_id,
                     "component_name": component_name,
                     "component_manager_id": component_manager_id,
                     "exclusive": exclusive,
                     "available": available,
                     "interfaces": interfaces}
    
    def add_interface(self, interface):
        if interface not in self.node["interfaces"]:
            self.node["interfaces"].append(interface)
    
    def clear_interfaces(self):
        self.node["interfaces"] = []
    
    def serialize(self):
        return self.node


class Link(object):
    def __init__(self, component_id, component_name, link_type=""):
        self.link = {"component_id": component_id,
                     "component_name": component_name,
                     "property": [],
                     "link_type": link_type,}
    
    def add_property(self, source, dest, capacity):
        self.link["property"].append(
            {"source_id": source, "dest_id": dest, "capacity": capacity})
    
    def serialize(self):
        return self.link
