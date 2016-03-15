from engine import MyPolicyEngine
from pypelib.utils.Logger import Logger

import os

logger = Logger.getLogger()


class PolicyManager:

    @staticmethod
    def evaluate_single_rule(rule):
        print "Policies > Manager > evaluating rule: ", rule
        if rule:
            logger.info("\nAdding a Rule to Policy Engine")
            pypelib_instance = MyPolicyEngine.getInstance()
            print "\n\n\n\n\npypelib_instance: ", pypelib_instance
            if pypelib_instance is not None:
                pypelib_instance.addRule(rule)
        logger.info("\nDumping table state...")
        logger.info("[RULETABLE]#################################")
        MyPolicyEngine.dump()
        logger.info("[RULETABLE]###############################\n")

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
    def evaluate_rules():
        rules = PolicyManager.read_rules()
        for rule in rules:
            PolicyManager.evaluate_single_rule(rule)
