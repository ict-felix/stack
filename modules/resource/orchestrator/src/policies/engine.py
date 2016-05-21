from threading import Lock
from policies.pypelib.RuleTable import RuleTable
from policies.pypelib.persistence.backends.rawfile.RAWFile import RAWFile

import os
import pickle


class PolicyEngine():
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
    _mappings = {
                "credential.expires":"metaObj['credential']['expires']",
                "credential.issuer_name":"metaObj['credential']['issuer_name']",
                "credential.owner_urn":"metaObj['credential']['owner_urn']",
                "request.REMOTE_ADDR":"metaObj['request']['REMOTE_ADDR']",
                "request.HTTP_USER_AGENT":"metaObj['request']['HTTP_USER_AGENT']",
                }

    @staticmethod
    def get_db_file_location():
        db_file_location = "db/policy_engine.db"
        try:
            current_file = os.path.realpath(__file__)
            current_location = os.path.dirname(os.path.realpath(__file__))
            ro_location = os.path.abspath(os.path.join(current_location, "..", ".."))
            db_file_location = os.path.join(ro_location, db_file_location)
        except:
            pass
        return db_file_location

    @staticmethod
    def get_instance():
        with PolicyEngine._mutex:
            if not PolicyEngine._instance:
                db_file_path = PolicyEngine.get_db_file_location()
                print "Loading ruletable from file..."
                PolicyEngine._instance = RuleTable.loadOrGenerate(
                    "PolicyEngine", PolicyEngine._mappings,
                    "RegexParser", "RAWFile", True, fileName=db_file_path)
        return PolicyEngine._instance

    @staticmethod
    def verify(obj):
        return PolicyEngine.get_instance().evaluate(obj)

    @staticmethod
    def dump():
        return PolicyEngine.get_instance().dump()
