# -*- coding: utf-8 -*-

# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kvm.KVMManager import KVMManager
from monitoring.MonitoringDispatcher import MonitoringDispatcher
from communications.XmlRpcClient import XmlRpcClient
from utils.Logger import Logger

class KVMMonitoringDispatcher(MonitoringDispatcher):
	
	logger = Logger.getLogger()
	
	# #Monitoring routines
	@staticmethod
	def listActiveVMs(vmid, server):
		try:		
			doms = KVMManager.retrieveActiveDomainsByUUID()
			XmlRpcClient.sendAsyncMonitoringActiveVMsInfo(vmid, "SUCCESS", doms, server)
		except Exception as e:
			# Send async notification
			XmlRpcClient.sendAsyncMonitoringActionStatus(vmid, "FAILED", str(e))
			KVMMonitoringDispatcher.logger.error(str(e))
		return
		
