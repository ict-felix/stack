from engine import PolicyEngine
from parser import Parser
from pypelib.persistence.backends.rawfile.RAWFile import RAWFile
from pypelib.RuleTable import RuleTable
from pypelib.utils.Logger import Logger
import os


class PolicyManager:

    @staticmethod
    def read_rules():
        rules = []
        policies_folder = os.path.dirname(os.path.realpath(__file__))
        base_folder = os.path.dirname(os.path.dirname(policies_folder))
        conf_folder = os.path.join(base_folder, "conf")
        try:
            f = open(os.path.join(conf_folder, "policies.txt"))
            rules = f.readlines()
            rules = [x.strip() for x in rules]
        except:
            pass
        return rules

    @staticmethod
    def store_rules(rules):
        for rule in rules:
            # Avoid comments
            if not rule.startswith("#"):
                print "Adding rule to Policy Engine: ", rule
                PolicyEngine.get_instance().addRule(rule)
        print "[RULETABLE]######################################################################"
        PolicyEngine.dump()
        print "[RULETABLE]######################################################################\n"

    @staticmethod
    def create_rule_table(default_policy=True):
        """
        Default policy set to True (whitelist).
        """
        # Generate a simple RuleTable and store (last param: default policy [True])
        rule_table= RuleTable("PolicyEngine", None, "RegexParser", "RAWFile", False, default_policy)
        RAWFile.save(rule_table, "RegexParser", fileName=PolicyEngine.get_db_file_location())

    @staticmethod
    def get_data_from_env(env_info):
        data_to_evaluate = []
        if env_info["request"]:
            data_to_evaluate.append(env_info["request"])
        if env_info["params"]:
            try:
                data_to_evaluate.append(env_info["params"][0][0]["geni_value"])
            except:
                pass
        return data_to_evaluate

    @staticmethod
    def evaluate_rules(default_policy=True, **env_info):
        return_val = False
        try:
            # Create table
            PolicyManager.create_rule_table(default_policy)
            # Read and store rules
            rules = PolicyManager.read_rules()
            PolicyManager.store_rules(rules)
            requests = PolicyManager.get_data_from_env(env_info)
            # Policies are enforced over a number of objects (creds, HTTP req, etc)
            for request in requests:
                # Parse request or credential only on appropriate methods
                # i.e. when not present, ignore
                dict_req = Parser.parse(request)
                # Invoke policy enforcement
                # - If not possible, evaluate to True (continue workflow)
                if dict_req:
                    return_val = PolicyEngine.verify(dict_req)
                else:
                    return_val = True
            return return_val
        except Exception as e:
            import traceback
            print traceback.print_exc()
            print "Error evaluating rules: ", e
