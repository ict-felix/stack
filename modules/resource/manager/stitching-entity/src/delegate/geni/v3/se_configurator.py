from delegate.geni.v3.db_manager_se import db_sync_manager

import os
import yaml

class seConfigurator:
    def __init__(self):

        # read from config file
        #stream = open("../conf/se-config.yaml", 'r')
        current_path = os.path.dirname(os.path.abspath( __file__ ))
        conf_file_path = os.path.join(current_path, "../../../../conf/se-config.yaml")
        stream = open(conf_file_path, "r")
        initial_config = yaml.load(stream)
        # self.configured_interfaces = initial_config["interfaces"]
        self.configured_interfaces = self.convert_config_into_Resources_datamodel(initial_config["interfaces"])
        self.initial_configured_interfaces = initial_config["interfaces"]

        # Push port status from configuration file into SE-db
        # TODO: Add other rspec parameters to db
        db_sync_manager.update_resources(self.configured_interfaces, fromConfigFile=True)

        self.component_id_prefix = initial_config["component_id"]
        self.component_manager_prefix = initial_config["component_manager_id"]
        self.vlan_trans = initial_config["vlan_trans"]
        self.qinq = initial_config["qinq"]
        self.capacity = initial_config["capacity"]

    def convert_config_into_Resources_datamodel(self, config):
        rm_datamodel = {}
        for interface in config:
            endpoints = config[interface]["remote_endpoints"]
            avail_vlans = {}
            for endpoint in endpoints:
                for vlan in endpoint["vlans"]:
                    if isinstance(vlan, int ):
                        avail_vlans[vlan] = True
                    else:
                        try:
                            v_start, v_end = vlan.split("-")
                            v_range = range(int(v_start), int(v_end)+1, 1)
                            for v in v_range:
                                avail_vlans[v] = True
                        except:
                            pass
            rm_datamodel[interface] = avail_vlans
        return rm_datamodel

    def get_ports_configuration(self):
        return self.configured_interfaces

    def set_ports_configuration(self, config):
        self.configured_interfaces = config

    def get_concrete_port_status(self, port):
        return self.configured_interfaces[port]

    def set_concrete_port_status(self, port, vlan, status):
        self.configured_interfaces[port][vlan] = status

    def check_available_resources(self, resources):

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        for resource in resources:
            try:
                r_splited = resource['port'].rsplit(":", 1)
                vlan = resource['vlan']
                component_id = r_splited[0]
                port = r_splited[1]
                vlans_result = self.get_concrete_port_status(port)
                result = vlans_result[vlan]
                if (result is False) or (component_id != self.component_id_prefix):
                    return False
            except KeyError:
                return False
        return True

    def set_resource_reservation(self, resources):
        for resource in resources:
            r_splited = resource['port'].rsplit(":", 1)
            vlan = resource['vlan']
            port = r_splited[1]
            self.set_concrete_port_status(port, vlan, False)
            
        # Update the SE-db
        db_sync_manager.update_resources(self.configured_interfaces)

    def free_resource_reservation(self, resources):
        for resource in resources:
            r_splited = resource['port'].rsplit(":", 1)
            vlan = resource['vlan']
            port = r_splited[1]
            self.set_concrete_port_status(port, vlan, True)
            
        # Update the SE-db
        db_sync_manager.update_resources(self.configured_interfaces)


    def get_nodes_dict_for_rspec(self):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        configured_interfaces = self.configured_interfaces
        vlan_trans = self.vlan_trans
        qinq = self.qinq

        # Prepare link capability translations
        link_trans_capability = 'urn:felix'
        if vlan_trans:
            link_trans_capability += '+vlan_trans'
        if qinq:
            link_trans_capability += '+QinQ'

        nodes = [
            {
                'component_manager_id': component_manager_prefix,
                'exclusive':'false',
                'interfaces':[],
                'component_id': component_id_prefix,
                'sliver_type_name':None
            }
        ]

        # Prepare nodes
        for iface in configured_interfaces:
            vlans_on_iface = configured_interfaces[iface]
            for vlan in vlans_on_iface:
                current_vlan_status = vlans_on_iface[vlan]
                if current_vlan_status is not False:
                    available_iface = {
                        'component_id': component_id_prefix + ':' + iface,
                        'vlan':[
                        ]
                    }
                    nodes[0]['interfaces'].append(available_iface)
                    break

        return nodes

    def get_links_dict_for_rspec(self):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        configured_interfaces = self.configured_interfaces
        vlan_trans = self.vlan_trans
        qinq = self.qinq
        capacity = self.capacity

        # Prepare link capability translations
        link_trans_capability = 'urn:felix'
        if vlan_trans:
            link_trans_capability += '+vlan_trans'
        if qinq:
            link_trans_capability += '+QinQ'

        links_se = [
            {
                'component_id': component_id_prefix + ':link',
                'component_manager_name': component_manager_prefix,
                'interface_ref':[
                    {
                        'component_id':'*'
                    },
                    {
                        'component_id':'*'
                    }
                ],
                'property':[
                    {
                        'source_id':'*',
                        'dest_id':'*',
                        'capacity': capacity
                    }
                ],
                'link_type': link_trans_capability
            }
        ]

        # Prepare links
        # TODO: add ports with vlan ranges in conf file
        config = self.initial_configured_interfaces
        for interface in config:
            endpoints = config[interface]["remote_endpoints"]
            avail_vlans = {}
            for endpoint in endpoints:
                for vlan in endpoint["vlans"]:
                    if isinstance(vlan, int ):
                        new_static_link =  {
                            'component_id':component_id_prefix + ':' + interface + "+" + endpoint["name"],
                            'component_manager_name':None,
                            'interface_ref':[
                                {
                                    'component_id': component_id_prefix + ':' + interface
                                },
                                {
                                    'component_id': endpoint["name"]
                                }
                            ],
                            'property':[

                            ],
                            'link_type':'urn:felix+' + endpoint["type"]
                        }
                        if configured_interfaces[interface][str(vlan)] == True:
                            links_se.append(new_static_link)
                            break
                    else:
                        try:
                            v_start, v_end = vlan.split("-")
                            v_range = range(int(v_start), int(v_end)+1, 1)
                            for v in v_range:
                                new_static_link =  {
                                    'component_id':component_id_prefix + ':' + interface + "+" + endpoint["name"],
                                    'component_manager_name':None,
                                    'interface_ref':[
                                        {
                                            'component_id': component_id_prefix + ':' + interface
                                        },
                                        {
                                            'component_id': endpoint["name"]
                                        }
                                    ],
                                    'property':[

                                    ],
                                    'link_type':'urn:felix+' + endpoint["type"]
                                }
                                if configured_interfaces[interface][str(vlan)] == True:
                                    links_se.append(new_static_link)
                                    break
                        except:
                            pass

        return links_se