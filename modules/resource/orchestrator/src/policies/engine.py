# from flask import request
from threading import Lock
from pypelib.RuleTable import RuleTable
# from interface.interface import MyInterface

import os


class MyPolicyEngine():
    """
    Uses pyPElib to build ONE RuleTable instance to apply policies to a
    certain scope (in this example, the interface)
    """

    # kind of Singleton pattern
    _instance = None
    _mutex = Lock()

    # Mappings contains the basic association between keywords and objects,
    # functions or static values
    # Note that these mappings are ONLY defined by the lib user (programmer)
    _mappings = {"cred.expires": "['credential']['expdate']"}

    @staticmethod
    def getInstance():
        with MyPolicyEngine._mutex:
            if not MyPolicyEngine._instance:
                print "Loading ruletable from File..."
                print "load or generate"
                policies_folder = os.path.dirname(os.path.realpath(__file__))
                db_folder = os.path.join(os.path.dirname(
                    os.path.dirname(policies_folder)), "db")
                print "> db_folder: ", db_folder
                db_name = "policy_engine.db"
                db_file = os.path.join(db_folder, db_name)
                db_dir = os.path.dirname(db_file)
                print "> db_dir: ", db_dir
                # Note: create file if it does not exist
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                if not os.path.exists(db_file):
                    open(db_file, "a").close()
                # Loading from database file backend
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> db_file: ", db_file
                # FIXME: check if parameter "fileName" is the path (db_file)
                # or name (db_name) of the database file. Check also if it
                # must be in the same folder as this file or can be located
                # under "db_dir"
                MyPolicyEngine._instance = RuleTable.loadOrGenerate(
                    "MyPolicyEngine", MyPolicyEngine._mappings,
                    "RegexParser", "RAWFile", True, fileName=db_file)
                print "Loaded and generated ", MyPolicyEngine._instance
        return MyPolicyEngine._instance

    @staticmethod
    def verify(obj):
        policy_instance = MyPolicyEngine.getInstance()
        # print "Policies > Engine > request: ", request.__dict__
        return policy_instance.evaluate(obj)

    @staticmethod
    def dump():
        policy_instance = MyPolicyEngine.getInstance()
        return policy_instance.dump()
