from vt_manager_kvm.controller.actions.ActionController import ActionController
from vt_manager_kvm.controller.drivers.VTDriver import VTDriver
from vt_manager_kvm.models.Action import Action
from vt_manager_kvm.models.VirtualMachine import VirtualMachine
import xmlrpclib, threading, logging, copy
from vt_manager_kvm.communication.utils.XmlHelper import XmlHelper
from vt_manager_kvm.models.resourcesHash import resourcesHash

class InformationDispatcher():

	@staticmethod
	def listResources(remoteHashValue, projectUUID = 'None', sliceUUID ='None'):
		logging.debug("Enter listResources")
		infoRspec = XmlHelper.getSimpleInformation()
		servers = VTDriver.getAllServers()
		baseVM = copy.deepcopy(infoRspec.response.information.resources.server[0].virtual_machine[0])
		if not servers:
			logging.debug("No VTServers available")
			infoRspec.response.information.resources.server.pop()
			resourcesString = XmlHelper.craftXmlClass(infoRspec)
			localHashValue = str(hash(resourcesString))
		else:
			for sIndex, server in enumerate(servers):
				if(sIndex == 0):
					baseServer = copy.deepcopy(infoRspec.response.information.resources.server[0])
				if(sIndex != 0):
					newServer = copy.deepcopy(baseServer)
					infoRspec.response.information.resources.server.append(newServer)
	
				InformationDispatcher.__ServerModelToClass(server, infoRspec.response.information.resources.server[sIndex] )
				if (projectUUID is not 'None'):
					vms = server.getVMs(projectId = projectUUID)
				else:
					vms = server.getVMs()
				if not vms:
					logging.debug("No VMs available")
					if infoRspec.response.information.resources.server[sIndex].virtual_machine:
						infoRspec.response.information.resources.server[sIndex].virtual_machine.pop()
				elif (sliceUUID is not 'None'):
					vms = vms.filter(sliceId = sliceUUID)
					if not vms:
						logging.error("No VMs available")
						infoRspec.response.information.resources.server[sIndex].virtual_machine.pop()
				for vIndex, vm in enumerate(vms):
					if (vIndex != 0):
						newVM = copy.deepcopy(baseVM)
						infoRspec.response.information.resources.server[sIndex].virtual_machine.append(newVM)
					InformationDispatcher.__VMmodelToClass(vm, infoRspec.response.information.resources.server[sIndex].virtual_machine[vIndex])
	
			resourcesString =   XmlHelper.craftXmlClass(infoRspec)
			localHashValue = str(hash(resourcesString))
		try:
			rHashObject =  resourcesHash.objects.get(projectUUID = projectUUID, sliceUUID = sliceUUID)
			rHashObject.hashValue = localHashValue
			rHashObject.save()
		except:
			rHashObject = resourcesHash(hashValue = localHashValue, projectUUID= projectUUID, sliceUUID = sliceUUID)
			rHashObject.save()
	
		if remoteHashValue == rHashObject.hashValue:
			return localHashValue, ''
		else:
			return localHashValue, resourcesString

	@staticmethod
	def listVMTemplatesInfo(serverUUID):
	#def listVMTemplatesInfo(serverUUID, callbackURL):
		logging.debug("Enter listVMTemplatesInfo")
		server = VTDriver.getServerByUUID(serverUUID)
		xmlrpc_server = xmlrpclib.Server(server.getAgentURL())
		templates_info = xmlrpc_server.list_vm_templates(server.getAgentPassword())
		#templates_info = xmlrpc_server.list_vm_templates(callbackURL, server.getAgentPassword())
		return str(templates_info)

        @staticmethod
        def forceListActiveVMs(serverID='None', vmID='None'):
                if serverID != 'None':
                    server = VTDriver.getServerById(serverID)
                    vtam_vms = server.getVMs()
                else: 
                    if vmID != 'None':
                        servers = VTDriver.getAllServers()
                        vtam_vms = list()
                        for server in servers:
                            vtam_vms = server.getVMs(id=int(vmID))
                            if vtam_vms:
                                vmID = vtam_vms[0].getUUID()
                                break
                        if not vtam_vms:
                            raise Exception("VM not found")
                xmlrpc_server = xmlrpclib.Server(server.getAgentURL())
                # Handle safely the connection against the agent
                try:
                    server_active_vms = xmlrpc_server.force_list_active_vms(server.getAgentPassword(), vmID)
                    updated_vms = list()
                    for vm in vtam_vms:
                        if vm.getUUID() in server_active_vms.keys():
                            vm.setState("running")
                            vm.save()
                        else:
                            # XXX: avoiding "on queue" and "unknown" states to avoid bad management
                            #if vm.getState() in ['deleting...', 'failed', 'on queue', 'unknown']:
                            if vm.getState() in ["deleting...", "failed"]:
                                child = vm.getChildObject()
                                server = vm.Server.get()
                                #Action.objects.all().filter(objectUUID = vm.uuid).delete()
                                server.deleteVM(vm)
                                # Keep actions table up-to-date after each deletion
                                vm_uuids = [ vm.uuid for vm in VirtualMachine.objects.all() ]
                                Action.objects.all().exclude(objectUUID__in = vm_uuids).delete()
                            elif vm.getState() in ["running", "starting...", "stopping..."] :
                                vm.setState("stopped")
                                vm.save()
                            else:
                                continue
                except:
                    server_active_vms = dict()
                return server_active_vms

	@staticmethod
	def __ServerModelToClass(sModel, sClass ):
		sClass.name = sModel.getName()
		#XXX: CHECK THIS
		sClass.id = sModel.id
		sClass.uuid = sModel.getUUID()
		sClass.operating_system_type = sModel.getOSType()
		sClass.operating_system_distribution = sModel.getOSDistribution()
		sClass.operating_system_version = sModel.getOSVersion()
		sClass.virtualization_type = sModel.getVirtTech()
		ifaces = sModel.getNetworkInterfaces()
		for ifaceIndex, iface in enumerate(ifaces):
			if ifaceIndex != 0:
				newInterface = copy.deepcopy(sClass.interfaces.interface[0])
				sClass.interfaces.interface.append(newInterface)
			if iface.isMgmt:
				sClass.interfaces.interface[ifaceIndex].ismgmt = True
			else:
				sClass.interfaces.interface[ifaceIndex].ismgmt = False
			sClass.interfaces.interface[ifaceIndex].name = iface.name   
			sClass.interfaces.interface[ifaceIndex].switch_id= iface.switchID   
			sClass.interfaces.interface[ifaceIndex].switch_port = iface.port  
 
	@staticmethod
	def __VMmodelToClass(VMmodel, VMxmlClass):

		VMxmlClass.name = VMmodel.getName()
		VMxmlClass.uuid = VMmodel.getUUID()
		VMxmlClass.status = VMmodel.getState()
		VMxmlClass.project_id = VMmodel.getProjectId()
		VMxmlClass.slice_id = VMmodel.getSliceId()
		VMxmlClass.project_name = VMmodel.getProjectName()
		VMxmlClass.slice_name = VMmodel.getSliceName()
		VMxmlClass.operating_system_type = VMmodel.getOSType()
		VMxmlClass.operating_system_version = VMmodel.getOSVersion()
		VMxmlClass.operating_system_distribution = VMmodel.getOSDistribution()
		VMxmlClass.virtualization_type = VMmodel.Server.get().getVirtTech()
		VMxmlClass.server_id = VMmodel.Server.get().getUUID()
		VMxmlClass.xen_configuration.hd_setup_type = VMmodel.getHdSetupType()
		VMxmlClass.xen_configuration.hd_origin_path = VMmodel.getHdOriginPath()
		VMxmlClass.xen_configuration.virtualization_setup_type = VMmodel.getVirtualizationSetupType()
		VMxmlClass.xen_configuration.memory_mb = VMmodel.getMemory()
		ActionController.PopulateNetworkingParams(VMxmlClass.xen_configuration.interfaces.interface, VMmodel)
