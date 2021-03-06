import pymongo
import threading

import core
logger = core.log.getLogger("db-manager")


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the SE mongo-db"""

    def __init__(self):
        self.__mutex = threading.Lock()

    # (felix_se) Resources
    def update_resources(self, resources={}, fromConfigFile=False):
        table = pymongo.MongoClient().felix_se.Resources
        
        # change int values in 'resources' keys into strings before pushing to db
        # if it's from yaml config file
        if fromConfigFile is True:
            logger.debug("Pushing configuration file into db")
            for port in resources:
                s_vlans = {}
                for vlan in resources[port]:
                    if isinstance(vlan, int ):
                        s_vlans[str(vlan)] = resources[port][vlan]
                    else:
                        s_vlans[vlan] = resources[port][vlan]
                resources[port] = s_vlans
        try:
            self.__mutex.acquire()
            table.update({"_id":"se_rm"},{"$set":{"status":resources}},upsert=True);
        finally:
            self.__mutex.release()

    def get_resources(self):
        table = pymongo.MongoClient().felix_se.Resources

        try:
            self.__mutex.acquire()
            row = table.find_one()
            if row is None:
                raise Exception("SEResources not found into SE-DB!")
            resources = row
        finally:
            self.__mutex.release()


        return resources["status"]

    # (felix_se) Slices
    
    def set_slices(self,sliceurn,resources):
        table = pymongo.MongoClient().felix_se.SliceResources
        try:
            self.__mutex.acquire()
            table.update({"sliceurn":sliceurn},{"sliceurn":sliceurn, "resources": resources},upsert=True)
        finally:
            self.__mutex.release()
    
    def get_slices(self,sliceurn):
        table = pymongo.MongoClient().felix_se.SliceResources
        
        try:
            self.__mutex.acquire()
            row = table.find_one({"sliceurn":sliceurn})
            
            if row is None:
                raise Exception("SESliceResources not found into SE-DB!")
           
            resources = row
            
        finally:
            self.__mutex.release()
        return resources["resources"]
            
    def remove_slices(self,sliceurn):
        table = pymongo.MongoClient().felix_se.SliceResources
        
        try:
            self.__mutex.acquire()
            table.remove({"sliceurn":sliceurn})
            
        finally:
            self.__mutex.release()


# This is the db manager object to be used into other modules
db_sync_manager = DBManager()
